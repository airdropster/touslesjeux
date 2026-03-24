# backend/tests/test_games.py
import pytest


@pytest.mark.asyncio
async def test_create_game(client):
    resp = await client.post("/api/games", json={
        "title": "Catan",
        "year": 1995,
        "designer": "Klaus Teuber",
        "theme": ["colonisation"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Catan"
    assert data["status"] == "enriched"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_list_games_empty(client):
    resp = await client.get("/api/games")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_games_with_data(client):
    await client.post("/api/games", json={"title": "Catan"})
    await client.post("/api/games", json={"title": "Azul"})
    resp = await client.get("/api/games")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_game(client):
    create = await client.post("/api/games", json={"title": "Catan"})
    game_id = create.json()["id"]
    resp = await client.get(f"/api/games/{game_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Catan"


@pytest.mark.asyncio
async def test_get_game_not_found(client):
    resp = await client.get("/api/games/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_game(client):
    create = await client.post("/api/games", json={"title": "Catan"})
    game_id = create.json()["id"]
    resp = await client.put(f"/api/games/{game_id}", json={"title": "Catan: Seafarers"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Catan: Seafarers"


@pytest.mark.asyncio
async def test_delete_game(client):
    create = await client.post("/api/games", json={"title": "Catan"})
    game_id = create.json()["id"]
    resp = await client.delete(f"/api/games/{game_id}")
    assert resp.status_code == 200
    resp = await client.get(f"/api/games/{game_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_games_stats(client):
    await client.post("/api/games", json={"title": "Catan"})
    resp = await client.get("/api/games/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_games_filter_by_status(client):
    await client.post("/api/games", json={"title": "Catan"})
    resp = await client.get("/api/games?status=enriched")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    resp = await client.get("/api/games?status=failed")
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_games_search(client):
    await client.post("/api/games", json={"title": "Catan"})
    await client.post("/api/games", json={"title": "Azul"})
    resp = await client.get("/api/games?search=catan")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_games_export(client):
    await client.post("/api/games", json={"title": "Catan"})
    resp = await client.get("/api/games/export")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
