import pytest
from sqlalchemy import select

from app.models import Game, Job


@pytest.mark.asyncio
async def test_create_job(db):
    job = Job(categories=["des", "familial"], target_count=100, status="pending")
    db.add(job)
    await db.commit()
    result = await db.execute(select(Job).where(Job.id == job.id))
    saved = result.scalar_one()
    assert saved.categories == ["des", "familial"]
    assert saved.target_count == 100
    assert saved.status == "pending"
    assert saved.processed_count == 0


@pytest.mark.asyncio
async def test_create_game(db):
    job = Job(categories=["des"], target_count=10, status="running")
    db.add(job)
    await db.commit()

    game = Game(
        title="Catan",
        year=1995,
        designer="Klaus Teuber",
        status="enriched",
        job_id=job.id,
        theme=["colonisation", "commerce"],
        mechanics=["dice_rolling", "trading"],
        core_mechanics=["trading"],
    )
    db.add(game)
    await db.commit()
    result = await db.execute(select(Game).where(Game.id == game.id))
    saved = result.scalar_one()
    assert saved.title == "Catan"
    assert saved.theme == ["colonisation", "commerce"]
    assert saved.job_id == job.id
