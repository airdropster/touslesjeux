# backend/tests/test_dedup.py
import pytest

from app.services.dedup import normalize_title, is_duplicate
from app.models import Game


def test_normalize_basic():
    assert normalize_title("Catan") == "catan"


def test_normalize_accents():
    assert normalize_title("Les Aventuriers du Rail") == "les aventuriers du rail"


def test_normalize_strip_edition():
    assert normalize_title("Catan Edition Deluxe") == "catan"


def test_normalize_strip_collector():
    assert normalize_title("Azul Collector's Edition") == "azul"


def test_normalize_case_insensitive():
    assert normalize_title("CATAN") == normalize_title("catan")


@pytest.mark.asyncio
async def test_is_duplicate_false(db):
    result = await is_duplicate(db, "Catan", 1995)
    assert result is False


@pytest.mark.asyncio
async def test_is_duplicate_true(db):
    game = Game(title="Catan", year=1995, status="enriched")
    db.add(game)
    await db.commit()
    result = await is_duplicate(db, "Catan", 1995)
    assert result is True


@pytest.mark.asyncio
async def test_is_duplicate_normalized(db):
    game = Game(title="Catan", year=1995, status="enriched")
    db.add(game)
    await db.commit()
    result = await is_duplicate(db, "CATAN", 1995)
    assert result is True
