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


@router.get("/debug/discover")
async def debug_discover():
    """Test discover_games end-to-end with minimal scope."""
    import time
    from app.services.scraper import discover_games, THROTTLE_SECONDS
    import app.services.scraper as scraper_mod
    # Temporarily reduce throttle for testing
    original = scraper_mod.THROTTLE_SECONDS
    scraper_mod.THROTTLE_SECONDS = 0.5
    try:
        start = time.time()
        games = await discover_games(["strategie"])
        elapsed = time.time() - start
        return {
            "elapsed_seconds": round(elapsed, 1),
            "game_count": len(games),
            "games": [{"title": g.title, "url": g.source_url} for g in games[:5]],
        }
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    finally:
        scraper_mod.THROTTLE_SECONDS = original


@router.get("/debug/openai")
async def debug_openai():
    """Test OpenAI API connectivity."""
    from openai import AsyncOpenAI
    from app.config import settings
    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'hello' in one word."}],
            max_tokens=5,
        )
        return {"status": "ok", "response": resp.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}"}
