# Exa + Jina Reader Scraper Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Google Custom Search API + BeautifulSoup with Exa semantic search + Jina Reader for board game discovery and page extraction.

**Architecture:** Rewrite `scraper.py` to use `exa_py` SDK (wrapped in `asyncio.to_thread`) for search and `httpx` calls to `r.jina.ai` for page reading. Public interface `discover_games() -> list[ScrapedGame]` is unchanged — no downstream changes needed.

**Tech Stack:** exa_py, httpx, asyncio

**Spec:** `docs/superpowers/specs/2026-03-29-exa-jina-scraper-design.md`

---

## Chunk 1: Replace Scraper

### Task 1: Update Dependencies and Config

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/config.py`
- Modify: `.env.example`

- [ ] **Step 1: Update pyproject.toml**

Replace `beautifulsoup4` with `exa_py`:

```toml
# In dependencies list, replace:
#   "beautifulsoup4>=4.12.0",
# With:
#   "exa-py>=1.0.0",
```

The full dependencies list becomes:

```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "httpx>=0.28.0",
    "exa-py>=1.0.0",
    "openai>=1.58.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "python-dotenv>=1.0.0",
    "slowapi>=0.1.9",
    "bleach>=6.2.0",
    "sse-starlette>=2.2.0",
]
```

- [ ] **Step 2: Update config.py**

Replace Google CSE fields with Exa + Jina:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://touslesjeux:changeme@localhost:5432/touslesjeux"
    openai_api_key: str = ""
    exa_api_key: str = ""
    jina_api_key: str = ""
    app_api_key: str = "changeme"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 3: Update .env.example**

```
OPENAI_API_KEY=sk-your-key-here
EXA_API_KEY=your-exa-api-key
JINA_API_KEY=your-jina-api-key
DB_USER=touslesjeux
DB_PASSWORD=changeme
DATABASE_URL=postgresql+asyncpg://touslesjeux:changeme@localhost:5432/touslesjeux
APP_API_KEY=changeme
CORS_ORIGINS=http://localhost:5173
```

- [ ] **Step 4: Install updated dependencies**

```bash
cd backend && pip install -e ".[dev]"
```

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/app/config.py .env.example
git commit -m "chore: replace Google CSE deps with exa-py, add Jina config"
```

---

### Task 2: Rewrite Scraper Tests (Red)

**Files:**
- Rewrite: `backend/tests/test_scraper.py`

- [ ] **Step 1: Write new test file**

```python
# backend/tests/test_scraper.py
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.scraper import (
    ScrapedGame,
    build_search_queries,
    clean_title,
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


# --- ScrapedGame ---

def test_scraped_game_dataclass():
    game = ScrapedGame(title="Catan", source_url="https://example.com/catan")
    assert game.title == "Catan"
    assert game.year is None
    assert game.raw_text == ""
    assert isinstance(game.scraped_at, datetime)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_scraper.py -v
```

Expected: FAIL — `clean_title`, `search_exa`, `read_page_jina` not found (old scraper still in place).

- [ ] **Step 3: Commit failing tests**

```bash
git add backend/tests/test_scraper.py
git commit -m "test: red — rewrite scraper tests for Exa + Jina"
```

---

### Task 3: Rewrite Scraper Implementation (Green)

**Files:**
- Rewrite: `backend/app/services/scraper.py`

- [ ] **Step 1: Rewrite scraper.py**

```python
# backend/app/services/scraper.py
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime

import httpx
from exa_py import Exa

from app.config import settings

logger = logging.getLogger(__name__)

THROTTLE_SECONDS = 2.0

# --- Exa client (lazy singleton) ---

_exa_client: Exa | None = None


def _get_exa() -> Exa:
    global _exa_client
    if _exa_client is None:
        if not settings.exa_api_key:
            raise RuntimeError("EXA_API_KEY not configured")
        _exa_client = Exa(api_key=settings.exa_api_key)
    return _exa_client


# --- Data ---

@dataclass
class ScrapedGame:
    title: str
    source_url: str
    year: int | None = None
    player_count_min: int | None = None
    player_count_max: int | None = None
    duration_min: int | None = None
    duration_max: int | None = None
    raw_text: str = ""
    scraped_at: datetime = field(default_factory=datetime.now)


# --- Helpers ---

def clean_title(raw: str) -> str:
    """Clean search result title by stripping site suffixes."""
    return raw.split(" - ")[0].split(" | ")[0].strip()


def build_search_queries(categories: list[str]) -> list[str]:
    templates = [
        "meilleurs jeux de societe {cat}",
        "top jeux de societe {cat}",
        "jeux de societe {cat} classement",
        "jeux de societe {cat} 2024 2025",
    ]
    queries = []
    for cat in categories:
        for tpl in templates:
            queries.append(tpl.format(cat=cat))
    return queries


# --- Search (Exa) ---

async def search_exa(query: str) -> list[dict]:
    """Semantic web search via Exa. Returns list of {url, title}."""
    exa = _get_exa()
    try:
        result = await asyncio.to_thread(exa.search, query, num_results=10, type="neural")
        return [{"url": r.url, "title": r.title} for r in result.results]
    except Exception as e:
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str:
            raise RuntimeError("Exa API key is invalid") from e
        logger.error("Exa search failed for '%s': %s", query, e)
        return []


# --- Page reading (Jina) ---

async def read_page_jina(url: str, max_length: int = 15000) -> str | None:
    """Fetch clean Markdown of a web page via Jina Reader."""
    jina_url = f"https://r.jina.ai/{url}"
    headers: dict[str, str] = {"Accept": "text/plain"}
    if settings.jina_api_key:
        headers["Authorization"] = f"Bearer {settings.jina_api_key}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(jina_url, headers=headers)
            if resp.status_code != 200:
                logger.warning("Jina returned %d for %s", resp.status_code, url)
                return None
            return resp.text[:max_length]
    except Exception as e:
        logger.warning("Jina read failed for %s: %s", url, e)
        return None


# --- Orchestration ---

async def discover_games(categories: list[str]) -> list[ScrapedGame]:
    """Discover board games by searching and reading pages."""
    queries = build_search_queries(categories)
    all_games: list[ScrapedGame] = []
    seen_urls: set[str] = set()

    for query in queries:
        try:
            results = await search_exa(query)
        except RuntimeError:
            raise  # Fatal errors (invalid key) propagate
        except Exception as e:
            logger.error("Search failed for '%s': %s", query, e)
            continue

        for item in results:
            url = item.get("url", "")
            if url in seen_urls or not url:
                continue
            seen_urls.add(url)

            await asyncio.sleep(THROTTLE_SECONDS)
            raw_text = await read_page_jina(url)
            if not raw_text:
                continue

            title = clean_title(item.get("title", ""))
            if not title:
                continue

            all_games.append(ScrapedGame(
                title=title,
                source_url=url,
                raw_text=raw_text,
            ))

    return all_games
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_scraper.py -v
```

Expected: ALL PASS

- [ ] **Step 3: Run full test suite to verify no regressions**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: ALL PASS (49+ tests). The collector, enricher, and other tests should not be affected since `discover_games` signature is unchanged.

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/scraper.py
git commit -m "feat: replace Google CSE + BeautifulSoup with Exa + Jina Reader"
```

---

### Task 4: Update Documentation

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CLAUDE.md environment variables table**

In the Environment Variables section, replace:

```
| `GOOGLE_CSE_API_KEY` | Google Custom Search Engine API key |
| `GOOGLE_CSE_CX` | Google Custom Search Engine ID |
```

With:

```
| `EXA_API_KEY` | Exa API key for web search |
| `JINA_API_KEY` | Jina Reader API key for page extraction |
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update env vars for Exa + Jina in CLAUDE.md"
```

---

## Task Summary

| Task | Component | Key Files |
|---|---|---|
| 1 | Dependencies + Config | `pyproject.toml`, `config.py`, `.env.example` |
| 2 | Tests (Red) | `tests/test_scraper.py` |
| 3 | Scraper rewrite (Green) | `services/scraper.py` |
| 4 | Documentation | `CLAUDE.md` |

**Dependencies:** Tasks are sequential: 1 → 2 → 3 → 4.
