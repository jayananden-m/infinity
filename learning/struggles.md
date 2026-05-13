## Code flow / ordering
- I understand WHAT code should do but struggle with the SEQUENCE
- Ordering if-checks: use "most restrictive first" / guard clause pattern
- Fix: write English pseudocode bullets before any Python
- Every path must end with STOP (return or raise)

## Wiring vs implementing
- Easy to implement domain logic in isolation; harder to wire it end-to-end
- Things that were implemented but not connected: skill update, Redis cache, LLM enqueue
- Fix: after implementing a component, immediately trace the call path from the API layer down

## What "E2E working" actually means
- "The app runs" ≠ "the adaptive loop is active"
- Session completed → skill update must be called or adaptation never evolves
- Lesson: integration is a separate concern from implementation

## localStorage is global
- Storing session history by key `tl_history` shared across all users on same browser
- New user saw old user's sessions — confusing
- Fix: namespace all localStorage keys by user ID decoded from JWT (`tl_history_<uuid>`)

## Cache as an anti-pattern when misused
- Redis cache set to 24h TTL + always returning `candidates[0]` → same passage every session
- Cache is meant for performance, not for locking in a value
- Fix: always query DB for candidates, pick randomly, only use cache as fallback when DB is empty

## EMA vs raw value
- Confused why dashboard showed 37 WPM when session WPM was 53
- EMA (alpha=0.3): `0.3 × 53 + 0.7 × 30 = 37` — new value is smoothed toward baseline
- "What you typed" vs "what the model thinks you can do" are different numbers — both correct
