# TypeLingo — User Guide

TypeLingo is a terminal-style application that improves your English and typing speed at the same time. Unlike a standard typing test, every session is built around what you personally need to work on — your vocabulary, your grammar weak spots, and your slowest keys. The more you use it, the more precisely it adapts to you.

---

## Getting Started

When you open TypeLingo, you land in a clean dark terminal. Every action starts with a `/` command. Press `/` anywhere on the screen to bring up the command bar, or just start typing directly.

### Accounts

You have three ways to get started:

**Guest mode** — `/guest`
Start immediately with no account. TypeLingo gives you a full session that lasts 7 days. Your vocabulary and progress persist during this window, but nothing carries over after it expires. Good for trying the app before committing.

**Register** — `/register`
Creates a permanent account. You'll be asked for your email, a display name, and a password in sequence. Once registered, your vocab library and skill profile are saved permanently.

**Login** — `/login`
Sign in to an existing account. Enter your email, then your password.

At any point, `/logout` signs you out.

---

## Choosing Your Level

The first time you sign in or enter guest mode, TypeLingo asks for your English level. It uses the CEFR scale — the international standard for English proficiency:

| Level | Description |
|---|---|
| A1 | Beginner — basic phrases and familiar words |
| A2 | Elementary — simple sentences, everyday topics |
| B1 | Intermediate — can handle most travel situations, describe experiences |
| B2 | Upper Intermediate — understands complex text, interacts fluently |
| C1 | Advanced — expresses ideas fluently with only occasional effort |
| C2 | Mastery — understands and uses the language with precision and nuance |

Type your level (e.g. `B2`) and press Enter. This sets the difficulty of your sessions and the vocabulary words you'll encounter. You can always re-enter this by signing out and back in.

---

## Navigation

TypeLingo is entirely command-driven. Press `/` to open the command bar. Press `Tab` to autocomplete a command. Press `Esc` to dismiss the bar without running anything.

| Command | What it does |
|---|---|
| `/type` | Pure typing test |
| `/session` | Adaptive learning session (random mode) |
| `/session mine` | Sentence mining session |
| `/session cloze` | Cloze (fill-in-the-blank) session |
| `/session drill` | Grammar drill session |
| `/vocab` | Learn a new vocabulary word |
| `/vocab <word>` | Look up a specific word |
| `/words` | Browse your vocab library |
| `/dashboard` | View your typing stats |
| `/help` | List all commands |
| `/clear` | Clear the screen |
| `/logout` | Sign out |

During any active session, press `Esc` or `Ctrl+C` to cancel and return to the home screen.

---

## `/type` — Typing Test

`/type` is the pure speed-and-accuracy test. A passage appears and you type it from start to finish. There is no learning objective here — this is about measuring your fingers.

**During the test:**
- Your live WPM updates as you type, shown in the top right
- Your error count is shown in red next to it
- A progress bar tracks how far through the passage you are
- Characters you've typed correctly appear in full brightness; mistakes show in red with a subtle underline
- Backspace corrects errors

**After completing:**
TypeLingo shows your:
- **WPM** — words per minute, calculated from when you pressed your first key to your last
- **Accuracy** — the percentage of characters you typed correctly
- **Grade** — S (Flawless, 97%+), A (Excellent, 93%+), B (Good, 85%+), or C (Keep going)

These results are saved to your dashboard so you can track improvement over time. Only `/type` results feed the dashboard — your learning sessions are tracked separately.

---

## `/session` — Adaptive Learning Sessions

Learning sessions are different from a typing test. They are built from your vocabulary, targeted at your grammar weak areas, and designed to make new knowledge stick — not just measure your fingers. TypeLingo has three learning modes.

Running `/session` with no argument picks one of the three modes at random. You can also request a specific mode directly.

> **Note:** If you haven't practiced any vocabulary words yet, mine and cloze sessions require at least a few words in your library first. Start with `/vocab` to build up your collection.

---

### `/session mine` — Sentence Mining

Sentence mining is the most research-backed way to build vocabulary. Rather than reading a word in isolation, you encounter it embedded in a full, natural sentence — providing context your memory can actually anchor to.

**How it works:**

The app takes words from your personal vocabulary library and generates a passage that weaves them in naturally. The words you're being tested on are highlighted in **amber** as you type, so you notice them in context without stopping.

**Phase 1 — Typing**
Type the full passage. The target words glow as you reach them. Your WPM and error count are tracked in real time.

**Phase 2 — Recall**
Once the typing is done, the recall phase begins automatically. Each target word gets its own screen. The sentence it appeared in is shown with the word blanked out — replaced by underscores that match the word's exact length. You type what you think the missing word is, then press Enter.

- **Correct:** the word fills in green and you advance to the next one
- **Wrong:** the correct answer is revealed in red, and you enter a brief penalty round — you must type the correct word once before moving on. This is deliberate: the act of typing a word you just got wrong is far more effective for memory than just seeing the answer

After all recall items are done, TypeLingo shows your typing stats and the words you mined.

---

### `/session cloze` — Cloze Recovery

Cloze is fill-in-the-blank testing. Each item presents a sentence from your vocabulary with one word removed. You must recall and type the missing word without any passage to read first — pure memory.

**How it works:**

Each sentence appears with a blank (`___`) where the target word should be. As you type, your answer fills into the blank in real time. Press Enter to check it.

A progress bar at the top tracks how many items you've completed. Your running correct count is shown next to it.

- **Correct:** the blank fills green and the next sentence loads after a brief pause
- **Wrong:** the correct answer appears in red, then a penalty round begins — type the correct word character-by-character to proceed. Each character turns green as you match it, or red if you miss

At the end, TypeLingo shows your score (e.g. `4 / 5`) and a grade. A perfect score is possible — aim for it.

**Why cloze works:**
Retrieving a word from memory (rather than recognising it) is significantly harder, and the difficulty is the point. Every successful retrieval strengthens the neural pathway for that word. Every failed retrieval, followed by the penalty round, creates a strong corrective memory.

---

### `/session drill` — Grammar Drill

Grammar drill targets a specific grammatical pattern you need to practice — present perfect, conditional clauses, passive voice, and so on. TypeLingo identifies which structures you find hardest based on your history and designs a focused 3-round session around one of them.

**The three rounds:**

**Round 1 — Model**
You're shown a sentence that demonstrates the grammar pattern perfectly. Type it as accurately as you can. This is encoding: your fingers and your language brain both absorb the structure simultaneously.

**Round 2 — Variation**
A different sentence using the same grammar pattern, but with different vocabulary and context. This prevents you from just memorising one sentence — you're practising the pattern itself.

**Round 3 — Produce**
The hardest round. You're shown a sentence stem — the beginning of a sentence — and must complete it correctly using the grammar pattern. The full sentence to type appears below, but the challenge is to internalise it before your fingers start moving.

Between rounds, a brief transition screen confirms the previous round is complete. The grammar target (e.g. `present perfect continuous`) is shown throughout so you always know what you're training.

After all three rounds, TypeLingo shows your WPM across the full drill and confirms the grammar pattern is logged to your profile.

---

## `/vocab` — Learning a Word

`/vocab` with no argument fetches a word chosen specifically for your CEFR level. `/vocab <word>` looks up a specific word you've chosen (e.g. `/vocab ephemeral`). TypeLingo uses word suggestion autocomplete — press Tab while typing a word to see suggestions, and Tab again to complete the first one.

**The vocabulary card** shows everything you need to truly know a word:

- **The word** — displayed large at the top with its part of speech and CEFR level
- **Definition** — a clear, precise explanation of what the word means
- **Etymology** — where the word comes from. Understanding roots makes related words easier to learn and remember
- **Register** — whether the word is formal, informal, literary, technical, or conversational. Knowing register means you'll never use a word in the wrong context
- **Contrast** — how this word differs from similar words that are commonly confused with it (e.g. *imply* vs *infer*, *affect* vs *effect*)
- **Example** — a full sentence showing the word used naturally
- **Memory hook** — a mnemonic or association that makes the word stick

**After reading the card**, press Enter to practice the word. A sentence appears with the word replaced by a blank. Type the full sentence — when you reach the blank, type the missing word from memory. Getting it right commits the word to your vocabulary library.

Press Esc at the card to skip practice and return to the home screen. The word is **not** added to your library until you complete the practice sentence.

---

## `/words` — Vocab Library

`/words` opens your personal vocabulary library as a visual word cloud.

Every word you've practiced is shown, arranged in a spiral pattern. **Advanced words (C2, C1) sit at the centre** — they're the hardest and most valuable, so they take the focal point. Easier words spiral outward. The further from the centre, the more beginner the word.

**Colour coding by level:**
- A1 — green
- A2 — teal
- B1 — blue
- B2 — indigo
- C1 — purple
- C2 — pink

Hover over any word to see its CEFR level and part of speech in the strip below the cloud. Click a word to open its full vocabulary card and practice it again.

A legend at the bottom shows how many words you have at each level, so you can see at a glance where your collection is concentrated.

Press Esc or Enter to close.

---

## `/dashboard` — Your Typing Stats

`/dashboard` shows your typing performance over time, drawn from every `/type` session you've completed.

**The stats grid** shows four figures at a glance:
- **Sessions** — total number of typing tests completed
- **Avg WPM** — your average speed across all sessions
- **Best WPM** — your personal best
- **Avg Acc** — your average accuracy

Below the grid, your **8 most recent sessions** are listed with WPM, accuracy, and the opening text of the passage so you can recall what you were typing.

Accuracy is colour-coded: 90% and above shows in green. Below that shows in the default colour, a visual prompt that there's room to improve.

Press Esc, Enter, or Ctrl+C to close the dashboard.

---

## How TypeLingo Adapts to You

TypeLingo tracks two separate skill profiles simultaneously.

**Your typing skill** covers your raw speed, keystroke accuracy, and which specific keys you consistently fumble. If you repeatedly mistype `q`, `x`, or `z`, those keys are flagged as weak — and future passages will include them more often.

**Your English skill** covers your grammar level, vocabulary range, and which grammatical structures you struggle with. If you consistently hesitate before certain word types or get drill rounds wrong on a particular pattern, those areas are flagged.

After every session, TypeLingo compares the two profiles. If your typing is significantly ahead of your English level, the next session will prioritise your English — harder vocabulary, more challenging grammar. If your English is ahead of your typing, the next session will focus on your fingers — faster passages, more targeted key practice.

If both skills are roughly balanced, TypeLingo gives both a slight stretch at the same time.

This means you are never wasting a session on something you've already mastered, and you are never overwhelmed by something too far beyond your current level. The system continuously finds the edge of your ability — and pushes just past it.

---

## Tips for Getting the Most Out of TypeLingo

**Build your vocab library first.** The mine and cloze sessions are built from your personal word collection. The more words you have practiced, the richer and more varied those sessions become. Try to practice at least one new word with `/vocab` every day.

**Use `/type` consistently for clean stats.** Your dashboard only tracks `/type` results. Run at least one typing test per session so your progress curve stays accurate and visible.

**Don't skip the penalty round.** When you get a recall or cloze item wrong, the penalty round feels like friction — that is the point. The act of typing the correct answer immediately after a failure is one of the most effective memory techniques known. Embrace it.

**Let the random `/session` surprise you.** The random dispatch picks whichever mode is best for your current state. Trusting it over always picking the same mode leads to more balanced improvement.

**Pay attention to the grammar target in drill sessions.** The pattern shown at the top of the drill screen tells you exactly what TypeLingo thinks you need to work on. If the same pattern keeps coming up across multiple sessions, that is the system telling you something worth listening to.

**Read the etymology and memory hook.** It takes 10 seconds and dramatically increases how long a new word stays with you. Etymology connects a new word to words you already know. A good memory hook gives your brain something to hang the word on.
