# Vocab & Learning Loop

How vocabulary words are fetched, generated, validated, and fed back into session modes as reinforcement.

## /vocab command flow (pool-based)

```mermaid
flowchart TD
    Cmd["/vocab → GET /vocab/next\n(no word arg)"] --> PoolCheck

    PoolCheck["Redis LPOP\nvocab_pool:&lt;CEFR_LEVEL&gt;"]
    PoolCheck -->|word popped| SizeCheck["check pool size"]
    PoolCheck -->|pool empty| Enqueue503

    SizeCheck -->|size < 5| CeleryTrigger["enqueue Celery refill task\n(async — does not block user)"]
    SizeCheck -->|size OK| ReturnWord

    CeleryTrigger --> ReturnWord["return word to frontend"]

    Enqueue503["enqueue refill task\nreturn 503 — try again"]

    ReturnWord --> LLMGen["Celery task: generate vocab words\nfor CEFR level via Groq LLM\n(llama-3.3-70b-versatile)"]
    LLMGen --> Datamuse["validate each candidate\nvia Datamuse API\n(rejects non-words)"]
    Datamuse -->|valid| RPush["Redis RPUSH\nvocab_pool:&lt;CEFR_LEVEL&gt;"]
    Datamuse -->|invalid| Discard[discard candidate]

    style Enqueue503 fill:#9b2335,color:#fff
    style ReturnWord fill:#2d6a4f,color:#fff
```

## /vocab \<word\> flow (on-demand specific word)

```mermaid
flowchart TD
    CmdWord["/vocab &lt;word&gt; → GET /vocab/next?word=&lt;word&gt;"] --> Datamuse2

    Datamuse2["Datamuse pre-validate\n/words?sp=&lt;word&gt;&max=1"]
    Datamuse2 -->|word not found| Reject["422 Unprocessable Entity\ndetail: word not recognised"]
    Datamuse2 -->|word valid| LLMDirect

    LLMDirect["Groq LLM: generate full vocab card\nfor the specific word"]
    LLMDirect --> Response["return VocabWordResponse\n{word, cefr_level, pos, definition,\netymology, register, contrast_note,\nmemory_hook, examples, sentence_stem,\nsentence_answer}"]

    style Reject fill:#9b2335,color:#fff
    style Response fill:#2d6a4f,color:#fff
```

## Vocab card → practice → record cycle

```mermaid
sequenceDiagram
    participant User
    participant Terminal
    participant API
    participant Redis

    User->>Terminal: /vocab (or /vocab &lt;word&gt;)
    Terminal->>API: GET /vocab/next [?word=X]
    API->>Redis: LPOP vocab_pool:&lt;CEFR&gt; (pool path)
    Redis-->>API: word data
    API-->>Terminal: VocabWordResponse

    Note over Terminal: mode → vocab_card\nshow: word, POS, CEFR, definition,\netymology, register, contrast note,\nmemory hook, examples

    User->>Terminal: Enter
    Note over Terminal: mode → vocab_session\nshow: word + definition header\nfirst example sentence with word blanked

    User->>Terminal: type example sentence
    Note over Terminal: PassageTyper — char-by-char\nblank word revealed as user types

    Terminal->>Terminal: onComplete called
    Terminal->>API: POST /vocab/practiced\n{word, cefr_level, pos}
    Note over Terminal: mode → idle\n"word committed to vocab model."
```

## How practiced words feed mine and cloze sessions

```mermaid
flowchart TD
    Practice["POST /vocab/practiced\nword stored in user_vocab_words table"] --> Pool["user's practiced word pool\n(PostgreSQL)"]

    Pool -->|/session mine| MineGen["backend fetches recent words\nGroq generates passage\ncontaining target words"]
    Pool -->|/session cloze| ClozeGen["backend fetches recent words\nGroq generates N sentences\none word blanked per sentence"]

    MineGen --> MineSession["MineTyper:\n1. type passage (words highlighted amber)\n2. recall phase (word blanked → user fills in)"]
    ClozeGen --> ClozeSession["ClozeTyper:\nN items in sequence\nidle → correct/wrong → penalty if wrong"]

    MineSession --> SkillUpdate["POST /sessions/{id}/complete\nmotor + cognitive skill updated (EMA α=0.3)"]
    ClozeSession --> SkillUpdate

    SkillUpdate --> AdaptNext["adaptation engine\nbuild next DifficultyVector\nbased on updated skill gap"]
```

## SRS reinforcement loop

```mermaid
flowchart LR
    VocabCard["vocab_card\nlearn word"] --> VocabSession["vocab_session\ntype example sentence"]
    VocabSession --> Recorded["word recorded\nPOST /vocab/practiced"]
    Recorded --> MineCloze["appears in mine / cloze\nsessions as target word"]
    MineCloze --> SkillGap["skill gap updated\n(EMA on motor + cognitive)"]
    SkillGap --> AdaptedSession["next session difficulty\ntailored to current gap"]
    AdaptedSession --> VocabCard
```

## Vocab pool key schema

| Redis key | Contents | TTL | Refill trigger |
|---|---|---|---|
| `vocab_pool:<CEFR>` e.g. `vocab_pool:B1` | list of serialised word objects | none (persistent list) | pool size < 5 after LPOP |

Datamuse pre-validation ensures every word in the pool is a real English word before LLM enrichment runs. This prevents the LLM from elaborating on malformed or hallucinated candidates.
