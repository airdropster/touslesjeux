# backend/tests/test_collections.py
import pytest

from app.models import Job


@pytest.fixture(autouse=True)
def mock_worker(monkeypatch):
    monkeypatch.setattr("app.worker.BackgroundWorker.start_job", lambda job_id: None)


@pytest.mark.asyncio
async def test_launch_collection(client, db):
    resp = await client.post("/api/collections/launch", json={
        "categories": ["des", "familial"],
        "target_count": 10,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["categories"] == ["des", "familial"]
    assert data["target_count"] == 10


@pytest.mark.asyncio
async def test_launch_collection_invalid_count(client):
    resp = await client.post("/api/collections/launch", json={
        "categories": ["des"],
        "target_count": 5,
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_collections(client, db):
    await client.post("/api/collections/launch", json={"categories": ["des"], "target_count": 10})
    resp = await client.get("/api/collections")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_collection(client, db):
    create = await client.post("/api/collections/launch", json={"categories": ["des"], "target_count": 10})
    job_id = create.json()["id"]
    resp = await client.get(f"/api/collections/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == job_id


@pytest.mark.asyncio
async def test_get_collection_not_found(client):
    resp = await client.get("/api/collections/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cancel_not_running(client, db):
    create = await client.post("/api/collections/launch", json={"categories": ["des"], "target_count": 10})
    job_id = create.json()["id"]
    resp = await client.post(f"/api/collections/{job_id}/cancel")
    assert resp.status_code in (200, 409)
