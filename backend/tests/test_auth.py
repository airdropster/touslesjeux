# backend/tests/test_auth.py
import pytest


@pytest.mark.asyncio
async def test_health_no_auth_required(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_protected_route_without_key():
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.get("/api/games")
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_protected_route_with_wrong_key():
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers={"X-API-Key": "wrong"}) as c:
        resp = await c.get("/api/games")
        assert resp.status_code == 403
