import pytest


@pytest.mark.asyncio()
async def test_health_returns_ok(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio()
async def test_ready_returns_ready(client):
    response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.asyncio()
async def test_metrics_returns_200_with_prometheus_content_type(client):
    response = await client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.asyncio()
async def test_metrics_response_contains_typelingo_metric(client):
    response = await client.get("/api/v1/metrics")
    assert b"typelingo_sessions_started_total" in response.content
