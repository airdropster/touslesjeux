# backend/tests/test_scraper.py
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.scraper import (
    ScrapedGame,
    build_search_queries,
    clean_title,
    extract_titles_from_page,
    read_page_jina,
    search_exa,
)


# --- clean_title ---

def test_clean_title_simple():
    assert clean_title("Catan") == "Catan"


def test_clean_title_strip_separator_dash():
    assert clean_title("Catan - Fiche jeu - Tric Trac") == "Catan"


def test_clean_title_strip_separator_pipe():
    assert clean_title("Catan | BoardGameGeek") == "Catan"


def test_clean_title_strip_both():
    assert clean_title("Catan - Edition Voyage | Philibert") == "Catan"


def test_clean_title_empty():
    assert clean_title("") == ""


def test_clean_title_whitespace():
    assert clean_title("  Catan  ") == "Catan"


# --- build_search_queries ---

def test_build_search_queries():
    queries = build_search_queries(["des", "familial"])
    assert len(queries) >= 4
    assert any("des" in q for q in queries)
    assert any("familial" in q for q in queries)


def test_build_search_queries_empty():
    assert build_search_queries([]) == []


# --- search_exa ---

@pytest.mark.asyncio
async def test_search_exa_returns_results():
    mock_result = MagicMock()
    mock_result.results = [
        MagicMock(url="https://example.com/catan", title="Catan - Fiche"),
        MagicMock(url="https://example.com/azul", title="Azul | BGG"),
    ]

    with patch("app.services.scraper._get_exa") as mock_get:
        mock_exa = MagicMock()
        mock_exa.search.return_value = mock_result
        mock_get.return_value = mock_exa

        results = await search_exa("jeux de societe des")

    assert len(results) == 2
    assert results[0]["url"] == "https://example.com/catan"
    assert results[0]["title"] == "Catan - Fiche"


@pytest.mark.asyncio
async def test_search_exa_no_key():
    with patch("app.services.scraper.settings") as mock_settings:
        mock_settings.exa_api_key = ""
        # Reset cached client
        import app.services.scraper as scraper_mod
        scraper_mod._exa_client = None

        with pytest.raises(RuntimeError, match="EXA_API_KEY"):
            await search_exa("test")


@pytest.mark.asyncio
async def test_search_exa_invalid_key():
    with patch("app.services.scraper._get_exa") as mock_get:
        mock_exa = MagicMock()
        mock_exa.search.side_effect = ValueError("Request failed with status code 401: Unauthorized")
        mock_get.return_value = mock_exa

        with pytest.raises(RuntimeError, match="Exa API key is invalid"):
            await search_exa("test")


# --- read_page_jina ---

@pytest.mark.asyncio
async def test_read_page_jina_success():
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = "# Catan\n\nA game about trading."

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await read_page_jina("https://example.com/catan")

    assert result == "# Catan\n\nA game about trading."


@pytest.mark.asyncio
async def test_read_page_jina_failure():
    mock_response = AsyncMock()
    mock_response.status_code = 404

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await read_page_jina("https://example.com/missing")

    assert result is None


@pytest.mark.asyncio
async def test_read_page_jina_truncation():
    long_text = "x" * 20000
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = long_text

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await read_page_jina("https://example.com/long", max_length=15000)

    assert result is not None
    assert len(result) == 15000


# --- extract_titles_from_page ---

@pytest.mark.asyncio
async def test_extract_titles_from_page_success():
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content='["Catan", "Azul", "Wingspan"]'))]

    with patch("app.services.scraper.AsyncOpenAI") as mock_cls, \
         patch("app.services.scraper.settings") as mock_settings:
        mock_settings.openai_api_key = "test-key"
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = mock_client

        titles = await extract_titles_from_page("Some text about board games")

    assert titles == ["Catan", "Azul", "Wingspan"]


@pytest.mark.asyncio
async def test_extract_titles_from_page_empty():
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="[]"))]

    with patch("app.services.scraper.AsyncOpenAI") as mock_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = mock_client

        titles = await extract_titles_from_page("No games here")

    assert titles == []


@pytest.mark.asyncio
async def test_extract_titles_from_page_api_error():
    with patch("app.services.scraper.AsyncOpenAI") as mock_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        mock_cls.return_value = mock_client

        titles = await extract_titles_from_page("Some text")

    assert titles == []


# --- ScrapedGame ---

def test_scraped_game_dataclass():
    game = ScrapedGame(title="Catan", source_url="https://example.com/catan")
    assert game.title == "Catan"
    assert game.year is None
    assert game.raw_text == ""
    assert isinstance(game.scraped_at, datetime)


# --- discover_games integration ---

@pytest.mark.asyncio
async def test_discover_games_integration():
    mock_result = MagicMock()
    mock_result.results = [
        MagicMock(url="https://example.com/catan", title="Catan - Fiche jeu"),
        MagicMock(url="https://example.com/azul", title="Azul | BGG"),
    ]

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = "Game description text here"

    async def mock_extract(raw_text):
        return ["Catan", "Azul"]

    with patch("app.services.scraper._get_exa") as mock_get, \
         patch("httpx.AsyncClient") as mock_client_cls, \
         patch("app.services.scraper.THROTTLE_SECONDS", 0), \
         patch("app.services.scraper.extract_titles_from_page", side_effect=mock_extract):
        mock_exa = MagicMock()
        mock_exa.search.return_value = mock_result
        mock_get.return_value = mock_exa

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        from app.services.scraper import discover_games
        games = await discover_games(["strategie"])

    assert len(games) >= 2
    titles = [g.title for g in games]
    assert "Catan" in titles
    assert "Azul" in titles
    assert all(g.raw_text == "Game description text here" for g in games)
    assert all(g.source_url for g in games)
