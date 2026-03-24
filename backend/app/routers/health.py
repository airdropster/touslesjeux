# backend/app/routers/health.py
from fastapi import APIRouter
from sqlalchemy import text

from app.database import async_session

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
async def health():
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {"status": "ok", "db": db_status}
