# TypeLingo Service Level Objectives (SLOs)

SLOs define the reliability commitments for the TypeLingo API.
They are measured over a rolling 30-day window.

## SLO Table

| SLO | Target | Measurement |
|---|---|---|
| API availability | 99.9% uptime | Health endpoint (`/api/v1/health`) success rate |
| Session start P99 latency | < 200 ms | `POST /api/v1/sessions` duration |
| Session complete P99 latency | < 300 ms | `POST /api/v1/sessions/{id}/complete` duration |
| WebSocket connection establishment | < 100 ms | WebSocket handshake time |
| LLM passage generation | < 10 s P95 | Celery task duration (Groq API call) |
| Error rate | < 0.1% | 5xx responses / total requests |

## Metrics Sources

- **Availability & error rate** — `typelingo_http_request_duration_seconds` labels `{status="5xx"}`
  reported to Prometheus via the `/api/v1/metrics` endpoint.
- **Latency** — same histogram, filtered by `path` label.
- **LLM task duration** — Celery task `typelingo_llm_passage_generation_seconds` histogram
  (to be added when the Celery task is implemented).
- **WebSocket latency** — measured client-side; logged via `ws.connected` structlog event.

## Alerting Thresholds

| Alert | Trigger |
|---|---|
| AvailabilityBreach | Error rate > 0.1% over 5 min |
| HighLatency | P99 session start > 200 ms over 5 min |
| LLMSlow | P95 Celery task > 10 s over 15 min |
