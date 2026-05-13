## Circuit breaker = Bouncer at a nightclub
- CLOSED = door open, letting people in, watching for trouble
- OPEN = door locked, reject everyone instantly
- HALF_OPEN = door cracked, testing one person
- Tally = counting troublemakers
- Timer = bouncer checking their watch

## Code ordering = Funnel
- Cheapest rejection first, expensive work last
- "What's the fastest reason to say no?" → put that first

## EMA (Exponential Moving Average) = Weather forecast
- Today's temperature doesn't reset your "average temperature for this city"
- Each new reading nudges the estimate — good sessions pull the model up slowly
- alpha=0.3 means "today counts for 30%, history counts for 70%"
- One freak cold day doesn't mean the city is cold — same with one fast typing session

## Cache = Post-it note on the fridge
- You checked the milk this morning — write it on a note so you don't have to check again
- Note expires (TTL) — after 24h you should check the fridge again
- If the note always says "skimmed milk" even when you bought whole milk, the note is the problem, not the fridge

## Hexagonal architecture = Theatre
- Domain (stage) = pure performance — no knowledge of who's in the audience or how the lights work
- API layer (front of house) = takes your ticket, shows you to your seat — doesn't write the play
- Infrastructure (backstage) = lights, props, sound — domain doesn't know these exist
- Ports (stage doors) = the only connection between stage and backstage — contracts, not implementations

## WebSocket = Phone call vs letter
- REST = send a letter, wait for a reply
- WebSocket = open phone call — both sides can talk at any time
- Session page keeps the call open; each keystroke is a word spoken into the phone

## Celery = Kitchen ticket system
- Waiter (API) takes the order, slaps a ticket on the rail, moves on
- Cook (Celery worker) sees the ticket when ready, makes the dish (calls Groq)
- Customer (user) doesn't wait at the counter — they're already at their table
- If the kitchen is slow, the ticket still gets done eventually

## JWT = Airport boarding pass
- Issued at check-in (login), contains your identity and expiry
- Anyone can read it (base64-encoded) — but can't fake the signature (HMAC secret)
- At the gate (middleware), they verify the signature — no database lookup needed
- Expires → get a new one at the refresh desk without re-entering your passport (POST /refresh)

## EMA skill update = Fitness tracker
- One great run doesn't make you an elite runner
- One bad run doesn't reset your fitness level
- The tracker averages your performance over time — recent sessions weighted more than old ones
