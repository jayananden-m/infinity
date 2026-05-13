# TypeLingo Metrics — Calculations & Data Flow

## 1. WPM (Words Per Minute)

### Formula
```
WPM = word_count(passage) / typing_duration_minutes
    capped at 300 (Math.min)
```

- **word_count**: `passage.split(/\s+/).filter(Boolean).length` — whitespace-split token count
- **typing_duration_minutes**: time from **first keystroke** to last character typed, in minutes

### Why "first keystroke", not "session start"
The session is created when `/session` is run. The user reads the passage before typing.
The timer starts in `PassageTyper` when `startedTyping.current === null` and the first printable
key is pressed, so reading time is excluded from the denominator.

### Completion contract
Sessions **only complete via auto-complete** — when `typed.length >= passage.length`.
The Enter key is a no-op in PassageTyper; pressing it mid-session does nothing.
To abandon a session, press Esc or Ctrl+C (returns to idle without recording).

`sessionComplete` also rejects any call where:
- `typed.length / passage.length < 0.8` — less than 80% of passage typed
- `durationMs < 3000` — under 3 seconds of actual typing time

These guards should never fire in normal use but prevent corrupt data from any future
edge-case path.

### Code path
```
PassageTyper.onKey()
  └─ first printable key → startedTyping.current = Date.now()
  └─ typed.length >= passage.length
       → duration = Date.now() - startedTyping.current
       → setTimeout(() => onComplete(typed, duration), 80)

useTerminal.sessionComplete(typed, durationMs)
  └─ guard: completionRate >= 0.8 && durationMs >= 3000
  └─ mins = durationMs / 60_000
  └─ wpm  = Math.min(wordCount / max(mins, 0.001), 300)
```

### Live WPM (PassageTyper stat bar)
Same formula, polled every 400 ms. Stays blank until `startedTyping` is set.

---

## 2. Accuracy

### Formula
```
accuracy = correct_chars / passage_length
```

- **correct_chars**: characters where `typed[i] === passage[i]` for `i < min(typed.length, passage.length)`
- **passage_length**: total characters in the passage (fixed denominator)

### Grade thresholds
| Grade | Accuracy |
|-------|----------|
| S     | > 97%    |
| A     | > 93%    |
| B     | > 85%    |
| C     | ≤ 85%    |

---

## 3. Dashboard Stats

All stats are computed from `SessionResult[]` stored in `localStorage` under `tl_history`.

| Stat         | Formula                                      |
|--------------|----------------------------------------------|
| sessions     | `history.length`                             |
| avg wpm      | `sum(wpm) / n`                               |
| best wpm     | `Math.max(...wpm)`                           |
| avg acc      | `sum(accuracy) / n * 100`  (accuracy is 0–1) |
| level        | CEFR level from last `/assess-english` run   |

### Data integrity filter (applied on load)
On `localStorage` load, sessions that fail `wpm >= 1 && wpm <= 300 && accuracy >= 0.05` are
stripped and the cleaned list is persisted back. This removes pre-fix sessions where pressing
Enter with no or minimal typing produced astronomically high WPM and zero accuracy.

Session history is capped at 60 entries (ring buffer via `slice(-60)` in `commitResult`).

---

## 4. CEFR Level

Determined by `/assess-english` and saved to `localStorage` under `tl_cefr`.
Displayed in the dashboard stats grid. Sent to the backend via `POST /api/v1/assess/complete`
(best-effort, non-blocking) to update the cognitive skill profile.

---

## 5. Data Flow

```
User keystroke
      │
      ▼
PassageTyper.onKey()
  ├─ Enter / Tab → preventDefault, ignored (no early exit)
  ├─ records startedTyping on first printable key
  ├─ updates typedRef + typed state
  ├─ live WPM polled every 400ms
  └─ typed.length >= passage.length
         → duration = now - startedTyping
         → setTimeout(onComplete(typed, duration), 80)
                    │
                    ▼
         useTerminal.sessionComplete()
           ├─ guard: 80% complete + 3s min
           ├─ wpm      = min(wordCount / mins, 300)
           ├─ correct  = chars where typed[i] === passage[i]
           ├─ accuracy = correct / passage.length
           ├─ grade    = S/A/B/C threshold
           ├─ commitResult() → localStorage
           └─ push() result lines to output


/vocab <word>
      │
      ▼
useTerminal.run()
  ├─ setOutput([])  +  setVocabLoading(true)
  ├─ await fetchVocabWord(token, word)
  │     └─ GET /api/v1/vocab/next?word=<word>
  ├─ setVocabLoading(false)
  ├─ setVocabWord(word)
  └─ setMode('vocab_card')      ← shows VocabCard component
         │
         ▼ (Enter)
    setMode('vocab_session')    ← shows vocabHeader + PassageTyper (minimal)
         │
         └─ onComplete → vocabSessionComplete()
               ├─ recordVocabPracticed(token, word, cefr, pos)
               │     └─ POST /api/v1/vocab/practiced → upsert user_vocab
               ├─ setOutput([committed message])
               └─ setMode('idle')


/vocab list
      │
      ▼
  await fetchVocabList(token)
    └─ GET /api/v1/vocab/list → SELECT * FROM user_vocab ORDER BY practiced_at DESC


/assess-english
      │
      ▼
  await fetchAssessQuestions(token)
    └─ GET /api/v1/assess/questions
         └─ Redis cache → fallback hardcoded questions → Celery queues LLM generation
  setMode('assess')           ← shows AssessQuestion component
         │
         └─ assessAnswer(selectedIndex)
               ├─ sets assessFeedback (shown 1.4s, auto-advances)
               ├─ or early stop if level ceiling hit
               └─ _finishAssessment()
                     ├─ POST /api/v1/assess/complete (best-effort)
                     ├─ setCefrLevel + localStorage.setItem('tl_cefr')
                     └─ setOutput([result lines])  +  setMode('idle')


/dashboard
      │
      ▼
  setMode('dashboard')        ← shows DashboardView component
  (reads history + cefrLevel from hook state, no fetch required)
  Esc / Enter to dismiss
```

---

## 6. Known Limitations

- **WPM uses passage word count, not 5-char standard**: industry standard is `(chars/5)/min`.
  Passage word count is used because it's more intuitive. A future v2 could add both.
- **Accuracy ignores backspace recovery**: corrected characters look correct in the final string.
  This matches most typing tests (net accuracy, not gross accuracy).
- **Session history is local**: `tl_history` lives in `localStorage`. Cross-device sync and
  server-side aggregation are not yet implemented.
- **Dashboard best WPM includes all stored sessions**: there is no per-session validation beyond
  the load-time filter. A user who somehow records a very high WPM in a valid session will see it.
