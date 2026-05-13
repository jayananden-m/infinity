# Session Modes

How `/session` dispatches to one of four modes, what each mode fetches and generates, and what results are shown on completion.

## Dispatch flowchart

```mermaid
flowchart TD
    Cmd["/session [arg]"] --> ArgCheck{arg present?}

    ArgCheck -->|no arg| Random["random.choice(['mine','cloze','drill'])"]
    ArgCheck -->|mine| Mine[mode = mine]
    ArgCheck -->|cloze| Cloze[mode = cloze]
    ArgCheck -->|drill| Drill[mode = drill]
    ArgCheck -->|unknown| Error["error: usage hint shown\nstay in idle"]

    Random --> Dispatch[POST /api/v1/sessions?mode=&lt;mode&gt;]
    Mine   --> Dispatch
    Cloze  --> Dispatch
    Drill  --> Dispatch

    Dispatch -->|400| NoVocab["error: practice /vocab first\n(mine/cloze require practiced words)"]
    Dispatch -->|503| NoPassage["error: generation queued\ntry again shortly"]
    Dispatch -->|200| Route{response.mode}

    Route -->|mine|  MineUI[session_mine mode]
    Route -->|cloze| ClozeUI[session_cloze mode]
    Route -->|drill| DrillUI[session_drill mode]
    Route -->|undefined| RegUI[session mode\nregular passage]
```

## Data flow: mine mode

```mermaid
sequenceDiagram
    participant Frontend
    participant API
    participant DB
    participant Groq

    Frontend->>API: POST /sessions?mode=mine (JWT)
    API->>DB: fetch user's recent practiced vocab words
    DB-->>API: list of words
    API->>Groq: generate passage containing target words\n(llama-3.3-70b-versatile)
    Groq-->>API: passage text with target words embedded
    API-->>Frontend: {id, mode:"mine", passage, target_words:[...]}

    Note over Frontend: render MineTyper\ntarget words highlighted amber
    Note over Frontend: typing phase → recall phase
    Frontend->>API: POST /sessions/{id}/complete\n{wpm, accuracy, duration_seconds}
```

## Data flow: cloze mode

```mermaid
sequenceDiagram
    participant Frontend
    participant API
    participant DB
    participant Groq

    Frontend->>API: POST /sessions?mode=cloze (JWT)
    API->>DB: fetch user's recent practiced vocab words
    DB-->>API: list of words
    API->>Groq: generate N sentences, one word blanked per sentence
    Groq-->>API: [{full, stem, answer}, ...]
    API-->>Frontend: {id, mode:"cloze", items:[{full,stem,answer}]}

    Note over Frontend: render ClozeTyper\none item at a time
    Note over Frontend: type answer → Enter to check
    Frontend->>API: POST /sessions/{id}/complete\n{wpm, accuracy, duration_seconds}
```

## Data flow: drill mode

```mermaid
sequenceDiagram
    participant Frontend
    participant API
    participant DB
    participant Groq

    Frontend->>API: POST /sessions?mode=drill (JWT)
    API->>DB: fetch cognitive profile (weak_areas)
    DB-->>API: weak_areas list (or CEFR defaults if empty)
    Note over API: pick random grammar_target from weak_areas
    API->>Groq: generate 3 rounds for grammar_target\n(model → vary → produce)
    Groq-->>API: [{round_type, text, stem?, target_word?}, ...]
    API-->>Frontend: {id, mode:"drill", rounds:[...], grammar_target}

    Note over Frontend: render DrillTyper\n3 rounds via PassageTyper
    Frontend->>API: POST /sessions/{id}/complete\n{wpm, accuracy:1.0, duration_seconds}
```

## Data flow: regular session

```mermaid
sequenceDiagram
    participant Frontend
    participant API
    participant DB
    participant Redis
    participant Celery
    participant Groq

    Frontend->>API: POST /sessions (no mode param, JWT)
    API->>DB: get motor + cognitive skill profiles
    API->>API: build + quantize DifficultyVector
    API->>DB: find_by_difficulty(vector, limit=10)
    alt DB has candidates
        DB-->>API: passages
        API->>API: random.choice(candidates)
        API->>Redis: SET cache_key TTL 24h
    else DB empty
        API->>Redis: GET cache_key
        alt Redis hit
            Redis-->>API: cached passage
        else Redis miss
            API->>Celery: enqueue generate_passage_task
            API-->>Frontend: 503 no passages available
            Celery->>Groq: generate passage (async ~0.8s)
            Groq-->>Celery: passage text
            Celery->>DB: save passage
            Celery->>Redis: SET cache_key
        end
    end
    API-->>Frontend: {id, passage_content, status:"started"}

    Note over Frontend: render PassageTyper
    Frontend->>API: POST /sessions/{id}/complete
```

## UX state machine: mine

```mermaid
stateDiagram-v2
    [*]         --> Typing   : session starts
    Typing      --> Recall   : passage fully typed (≥80% completion)
    Typing      --> [*]      : Esc / Ctrl+C → abandon

    Recall      --> RecallIdle
    RecallIdle  --> RecallCorrect : Enter, answer matches word
    RecallIdle  --> RecallWrong   : Enter, answer wrong
    RecallCorrect --> RecallIdle  : advance to next word (800ms delay)
    RecallWrong   --> RecallPenalty : 900ms delay
    RecallPenalty --> RecallIdle  : penalty word typed correctly → advance
    RecallIdle  --> Done          : last word answered
    Done        --> [*]           : sessionMineComplete called
    Recall      --> [*]           : Esc / Ctrl+C → abandon
```

## UX state machine: cloze

```mermaid
stateDiagram-v2
    [*]      --> ItemIdle  : session starts (item 0)
    ItemIdle --> Correct   : Enter, input matches answer
    ItemIdle --> Wrong     : Enter, input does not match
    Correct  --> ItemIdle  : advance to next item (700ms delay)
    Wrong    --> Penalty   : 900ms delay
    Penalty  --> ItemIdle  : penalty word typed → advance
    ItemIdle --> Done      : last item answered
    Done     --> [*]       : sessionClozeComplete called
    ItemIdle --> [*]       : Esc / Ctrl+C → abandon
```

## UX state machine: drill

```mermaid
stateDiagram-v2
    [*]       --> Round1  : session starts
    Round1    --> Round2  : round 1 typed (PassageTyper onComplete)
    Round2    --> Round3  : round 2 typed
    Round3    --> Done    : round 3 typed
    Done      --> [*]     : sessionDrillComplete called
    Round1    --> [*]     : Esc / Ctrl+C → abandon
    Round2    --> [*]     : Esc / Ctrl+C → abandon
    Round3    --> [*]     : Esc / Ctrl+C → abandon

    note right of Round1 : round_type = model\n(encode the pattern)
    note right of Round2 : round_type = vary\n(same grammar, different context)
    note right of Round3 : round_type = produce\n(complete from stem)
```

## Results output per mode

| Mode | Metrics shown | Stored in tl_history |
|---|---|---|
| regular | wpm, accuracy, grade (S/A/B/C) | yes |
| mine | wpm, accuracy, words mined list | yes |
| cloze | score (N/total), grade (S/A/B/C) | no |
| drill | grammar_target, rounds complete (3/3), wpm | no |
