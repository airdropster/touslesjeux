# backend/app/routers/games.py
import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.database import get_db
from app.models import Game
from app.schemas import GameCreate, GameOut, GameUpdate

router = APIRouter(prefix="/api/games", tags=["games"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=dict)
async def list_games(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = None,
    search: str | None = None,
    type_jeu_famille: str | None = None,
    theme: str | None = None,
    min_players: int | None = None,
    max_players: int | None = None,
    complexity_min: int | None = None,
    complexity_max: int | None = None,
    public: str | None = None,
    sort: str = "created_at",
):
    query = select(Game)
    count_query = select(func.count(Game.id))

    if status:
        query = query.where(Game.status == status)
        count_query = count_query.where(Game.status == status)
    if search:
        pattern = f"%{search}%"
        search_filter = Game.title.ilike(pattern) | Game.designer.ilike(pattern) | Game.editeur.ilike(pattern)
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    if min_players is not None:
        query = query.where(Game.player_count_min >= min_players)
        count_query = count_query.where(Game.player_count_min >= min_players)
    if max_players is not None:
        query = query.where(Game.player_count_max <= max_players)
        count_query = count_query.where(Game.player_count_max <= max_players)
    if complexity_min is not None:
        query = query.where(Game.complexity_score >= complexity_min)
        count_query = count_query.where(Game.complexity_score >= complexity_min)
    if complexity_max is not None:
        query = query.where(Game.complexity_score <= complexity_max)
        count_query = count_query.where(Game.complexity_score <= complexity_max)
    # JSONB filters — use cast + contains for PostgreSQL (@> operator)
    # Note: these filters are PostgreSQL-only; SQLite tests should not exercise them
    if type_jeu_famille:
        query = query.where(Game.type_jeu_famille.contains([type_jeu_famille]))
        count_query = count_query.where(Game.type_jeu_famille.contains([type_jeu_famille]))
    if theme:
        query = query.where(Game.theme.contains([theme]))
        count_query = count_query.where(Game.theme.contains([theme]))
    if public:
        query = query.where(Game.public.contains([public]))
        count_query = count_query.where(Game.public.contains([public]))

    # Sorting
    sort_col = getattr(Game, sort, Game.created_at)
    query = query.order_by(sort_col.desc())

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    games = result.scalars().all()

    return {
        "items": [GameOut.model_validate(g).model_dump() for g in games],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total > 0 else 0,
    }


@router.get("/stats")
async def games_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Game.id)))).scalar() or 0
    enriched = (await db.execute(select(func.count(Game.id)).where(Game.status == "enriched"))).scalar() or 0
    skipped = (await db.execute(select(func.count(Game.id)).where(Game.status == "skipped"))).scalar() or 0
    failed = (await db.execute(select(func.count(Game.id)).where(Game.status == "failed"))).scalar() or 0
    return {"total": total, "enriched": enriched, "skipped": skipped, "failed": failed}


@router.get("/export")
async def export_games(db: AsyncSession = Depends(get_db), status: str | None = None):
    query = select(Game)
    if status:
        query = query.where(Game.status == status)
    result = await db.execute(query)
    games = result.scalars().all()
    return [GameOut.model_validate(g).model_dump() for g in games]


@router.get("/{game_id}", response_model=GameOut)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.post("", response_model=GameOut, status_code=201)
async def create_game(data: GameCreate, db: AsyncSession = Depends(get_db)):
    game = Game(**data.model_dump(), status="enriched")
    db.add(game)
    await db.commit()
    await db.refresh(game)
    return game


@router.put("/{game_id}", response_model=GameOut)
async def update_game(game_id: int, data: GameUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(game, key, value)
    await db.commit()
    await db.refresh(game)
    return game


@router.delete("/{game_id}")
async def delete_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    await db.delete(game)
    await db.commit()
    return {"detail": "Game deleted"}


@router.post("/{game_id}/reprocess")
async def reprocess_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status not in ("skipped", "failed"):
        raise HTTPException(status_code=409, detail="Game is not in skipped or failed status")
    game.status = "pending"
    game.skip_reason = None
    await db.commit()
    return {"detail": "Game queued for reprocessing"}
