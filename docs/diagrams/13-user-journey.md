# User Journey

End-to-end flows from first visit through the three auth paths, level selection gate, and the core usage loop connecting sessions, vocab learning, and skill adaptation.

## First visit: three auth paths

```mermaid
flowchart TD
    FirstVisit["First visit\nboot sequence — idle mode"] --> Choice{pick a path}

    Choice -->|/guest| Guest["POST /auth/guest\nJWT (7-day TTL)\ntl_auth → localStorage"]
    Choice -->|/login| Login["login_email → login_password\nPOST /auth/login\ntl_auth → localStorage"]
    Choice -->|/register| Register["reg_email → reg_name → reg_password\nPOST /auth/register\ntl_auth → localStorage"]

    Guest    --> LevelGate
    Login    --> LevelGate
    Register --> LevelGate

    LevelGate{tl_cefr in localStorage?}
    LevelGate -->|yes — returning user| UsageLoop
    LevelGate -->|no — new user| LevelSelect

    LevelSelect["level_select mode\nA1 · A2 · B1 · B2 · C1 · C2\nPOST /assess/complete\ntl_cefr → localStorage"]
    LevelSelect --> UsageLoop
```

## Core usage loop

```mermaid
flowchart TD
    UsageLoop[idle — ready] --> SessionPath
    UsageLoop --> VocabPath
    UsageLoop --> DashPath

    SessionPath["/session [mode]"] --> SessionStart["POST /sessions?mode=&lt;mode&gt;\npassage / items / rounds fetched"]
    SessionStart --> ActiveSession["active session\n(PassageTyper / MineTyper / ClozeTyper / DrillTyper)"]
    ActiveSession --> Complete["session complete\nPOST /sessions/{id}/complete"]
    Complete --> SkillUpdate["motor + cognitive skill updated\n(EMA α=0.3)\nresults printed to terminal"]
    SkillUpdate --> UsageLoop

    VocabPath["/vocab [word]"] --> VocabCard["GET /vocab/next\nvocab_card mode\nfull word metadata displayed"]
    VocabCard --> PracticeChoice{Enter or Esc}
    PracticeChoice -->|Enter| VocabSession["vocab_session mode\ntype example sentence"]
    PracticeChoice -->|Esc| UsageLoop
    VocabSession --> Recorded["POST /vocab/practiced\nword added to user pool"]
    Recorded --> UsageLoop

    DashPath["/dashboard"] --> DashView["DashboardView\nGET /users/me/skills\nmotor + cognitive stats\nsession history from tl_history"]
    DashView --> UsageLoop
```

## How the three session modes connect to vocab learning

```mermaid
flowchart LR
    VocabPractice["vocab_session\ntype example sentence\nPOST /vocab/practiced"] --> WordPool

    WordPool["user's practiced word pool\n(PostgreSQL)"]

    WordPool -->|/session mine| Mine["session_mine\npassage with target words\nhighlighted amber\n+ recall phase"]
    WordPool -->|/session cloze| Cloze["session_cloze\nN sentences\none blank per sentence\nfill-in + penalty"]

    Mine  --> Results["session complete\nwpm / accuracy / words mined"]
    Cloze --> Results

    SubGraph["(no vocab dependency)"]
    SubGraph -->|/session drill| Drill["session_drill\ngrammar drill\n3 rounds: model → vary → produce\nbased on cognitive weak_areas"]
    Drill --> Results
```

## Learning feedback loop

```mermaid
flowchart TD
    VocabLearn["learn word\nvocab_card → vocab_session"] --> WordAdded["word recorded\nPOST /vocab/practiced"]
    WordAdded --> Reinforce["reinforcement sessions\nmine: type in context\ncloze: recall from blank"]
    Reinforce --> SessionDone["session complete\nmotor + cognitive EMA updated"]
    SessionDone --> AdaptEngine["adaptation engine\ncompare motor_level vs cognitive_level"]

    AdaptEngine -->|motor weaker| ChallengMotor["CHALLENGE_MOTOR\nfaster passages, weak-key focus"]
    AdaptEngine -->|cognitive weaker| ChallengCog["CHALLENGE_COGNITIVE\ngrammar drill, harder vocab"]
    AdaptEngine -->|balanced| BothAdvance["BALANCED_ADVANCE\nboth skills +slight stretch"]

    ChallengMotor --> NewVector["new DifficultyVector\nquantized → passage selector"]
    ChallengCog   --> NewVector
    BothAdvance   --> NewVector

    NewVector --> NextSession["next session\ntailored to current skill gap"]
    NextSession --> VocabLearn
```

## Guest path constraints

```mermaid
flowchart TD
    GuestUser["guest user\n(POST /auth/guest)"] --> SameFeatures["full feature access\nsame as registered user"]
    SameFeatures --> GuestLimits["limits:\n— JWT expires in 7 days\n— tl_history in localStorage only\n— Celery cleanup task removes guest data after TTL"]
    GuestLimits --> Upgrade["upgrade: /register\ncreates permanent account\n(history not migrated)"]
```
