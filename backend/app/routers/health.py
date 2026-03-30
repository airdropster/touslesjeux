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


@router.get("/debug/scraper")
async def debug_scraper():
    """Temporary debug endpoint to test Exa + Jina."""
    from app.services.scraper import search_exa, read_page_jina
    errors = []
    exa_results = []
    jina_result = None

    try:
        exa_results = await search_exa("meilleurs jeux de societe strategie")
    except Exception as e:
        errors.append(f"exa: {type(e).__name__}: {e}")

    if exa_results:
        try:
            jina_result = await read_page_jina(exa_results[0]["url"], max_length=200)
        except Exception as e:
            errors.append(f"jina: {type(e).__name__}: {e}")

    return {
        "exa_count": len(exa_results),
        "exa_results": exa_results[:3],
        "jina_snippet": jina_result[:200] if jina_result else None,
        "errors": errors,
    }
