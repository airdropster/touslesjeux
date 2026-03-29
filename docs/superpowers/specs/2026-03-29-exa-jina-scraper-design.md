# Replace Google CSE + BeautifulSoup with Exa + Jina Reader

## Overview

Replace the scraper's search and page reading layers. Google Custom Search API becomes Exa semantic search. httpx+BeautifulSoup+allowlist becomes Jina Reader. The scraper's public interface (`discover_games() -> list[ScrapedGame]`) stays identical — downstream code (collector, enricher) is unaffected.

Motivated by: Google CSE's 100 queries/day free limit constrains large collection jobs. Exa is free, has no hard daily limit, and its semantic search is better suited for finding board game content. Jina Reader returns clean Markdown without needing domain-specific HTML extractors.

## What changes

### Removed

- `search_google_cse()` — replaced by `search_exa()`
- `scrape_page()`, `_check_robots()`, `_is_public_ip()`, `is_allowed_url()` — replaced by `read_page_jina()`
- `extract_game_titles_from_html()`, `sanitize_html()` — Jina returns clean Markdown
- `ALLOWED_DOMAINS`, `_robots_cache` — Jina handles access rules server-side
- `beautifulsoup4` dependency from `pyproject.toml`
- `GOOGLE_CSE_API_KEY` and `GOOGLE_CSE_CX` from config and `.env.example`

### Added

- `exa_py` dependency in `pyproject.toml`
- `EXA_API_KEY` env var in `.env.example` and `config.py`
- `search_exa(query: str) -> list[dict]` — calls Exa Python SDK, returns search results with URLs, titles, snippets
- `read_page_jina(url: str, max_length: int = 15000) -> str | None` — HTTP GET to `https://r.jina.ai/{url}`, returns clean Markdown text truncated to max_length

### Unchanged

- `ScrapedGame` dataclass — same fields, same interface
- `build_search_queries(categories)` — same query templates
- `discover_games(categories) -> list[ScrapedGame]` — same signature and contract
- `THROTTLE_SECONDS` — same 2s delay between requests
- All downstream code: collector.py, enricher.py, dedup.py, worker.py, routers

## New scraper architecture

```
discover_games(categories: list[str]) -> list[ScrapedGame]
  build_search_queries(categories)
  for each query:
    search_exa(query) -> list of {url, title, snippet}
  dedupe URLs
  for each unique result:
    read_page_jina(url) -> clean Markdown text (or None on failure)
    yield ScrapedGame(title, source_url, raw_text)
```

## search_exa()

Uses the `exa_py` SDK:

```python
from exa_py import Exa

async def search_exa(query: str) -> list[dict]:
    exa = Exa(api_key=settings.exa_api_key)
    result = exa.search(query, num_results=10, type="neural")
    return [{"url": r.url, "title": r.title} for r in result.results]
```

Exa's `search()` is synchronous. Wrap in `asyncio.to_thread()` to avoid blocking the event loop.

## read_page_jina()

Simple HTTP call:

```python
async def read_page_jina(url: str, max_length: int = 15000) -> str | None:
    jina_url = f"https://r.jina.ai/{url}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(jina_url, headers={"Accept": "text/plain"})
        if resp.status_code != 200:
            return None
        return resp.text[:max_length]
```

No allowlist, no robots.txt check, no HTML parsing needed. Jina handles all of that. The `Accept: text/plain` header requests Markdown output.

## Config changes

### config.py

```python
# Remove:
google_cse_api_key: str = ""
google_cse_cx: str = ""

# Add:
exa_api_key: str = ""
```

### .env.example

```
# Remove:
GOOGLE_CSE_API_KEY=...
GOOGLE_CSE_CX=...

# Add:
EXA_API_KEY=your-exa-api-key
```

## Error handling

| Error | Strategy |
|---|---|
| Exa 401 (invalid key) | FATAL — raise `RuntimeError`, job marked `failed` |
| Exa 429 (rate limit) | Exponential backoff: 5s, 15s, 45s. Retry same query |
| Exa 500/503 | Retry x3 with backoff, then skip query |
| Jina timeout | Skip URL, continue to next |
| Jina 4xx/5xx | Skip URL, log warning, continue |

These match the existing error handling patterns from the Google CSE implementation.

## Dependencies

### pyproject.toml changes

```toml
# Remove:
"beautifulsoup4>=4.12.0",

# Add:
"exa_py>=1.0.0",

# Keep (still used by enricher for output sanitization):
"httpx>=0.28.0",
```

Note: `bleach` is used by `enricher.py` for sanitizing AI output, not by the scraper. It stays (or gets replaced by `nh3` separately).

## Tests

Rewrite `backend/tests/test_scraper.py`:

- `test_build_search_queries` — unchanged
- `test_search_exa_returns_results` — mock Exa SDK, verify result format
- `test_search_exa_invalid_key` — mock 401, verify RuntimeError raised
- `test_read_page_jina_success` — mock httpx, verify Markdown returned
- `test_read_page_jina_failure` — mock httpx error, verify None returned
- `test_read_page_jina_truncation` — verify max_length enforcement
- `test_discover_games_integration` — mock both Exa + Jina, verify ScrapedGame list

Remove tests for: `is_allowed_url`, `sanitize_html`, `_is_public_ip`, `ALLOWED_DOMAINS`.

## Files affected

| File | Change |
|---|---|
| `backend/app/services/scraper.py` | Rewrite — replace Google CSE + BeautifulSoup with Exa + Jina |
| `backend/app/config.py` | Remove google_cse fields, add exa_api_key |
| `backend/pyproject.toml` | Remove beautifulsoup4, add exa_py |
| `backend/tests/test_scraper.py` | Rewrite tests for new implementation |
| `.env.example` | Remove Google CSE vars, add EXA_API_KEY |
| `CLAUDE.md` | Update env vars table |

No changes to: collector.py, enricher.py, dedup.py, worker.py, routers, frontend.
