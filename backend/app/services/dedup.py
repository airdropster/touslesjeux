# backend/app/services/dedup.py
import re
import unicodedata

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Game

STRIP_WORDS = {"edition", "editions", "deluxe", "collector", "collectors", "limited", "anniversary", "big", "box"}


def normalize_title(title: str) -> str:
    text = title.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation BEFORE strip-words check
    words = text.split()
    words = [w for w in words if w not in STRIP_WORDS]
    text = " ".join(words)
    text = re.sub(r"\s+", " ", text).strip()
    return text


async def is_duplicate(db: AsyncSession, title: str, year: int | None) -> bool:
    # Hard check: exact match on DB constraint (LOWER(title) + COALESCE(year, 0))
    result = await db.execute(
        select(Game.id).where(
            func.lower(Game.title) == title.lower(),
            func.coalesce(Game.year, 0) == (year or 0),
        ).limit(1)
    )
    if result.scalar_one_or_none() is not None:
        return True
    # Soft check: normalized title search using ILIKE with first word
    normalized = normalize_title(title)
    first_word = normalized.split()[0] if normalized else ""
    if not first_word:
        return False
    candidates = await db.execute(
        select(Game.title, Game.year).where(Game.title.ilike(f"%{first_word}%"))
    )
    for row in candidates.all():
        if normalize_title(row.title) == normalized:
            return True
    return False
