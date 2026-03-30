# backend/app/services/scraper.py
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

import httpx
from exa_py import Exa
from openai import AsyncOpenAI

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


_LISTICLE_PATTERNS = [
    "meilleur", "top ", "classement", "sélection", "selection",
    "notre avis", "comparatif", "guide d'achat", "incontournable",
    "les plus", "jeux de société",
]


def is_listicle_title(title: str) -> bool:
    """Return True if a title looks like an article/listicle, not a game name."""
    lower = title.lower().strip()
    if len(lower) > 60:
        return True
    return any(p in lower for p in _LISTICLE_PATTERNS)


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
    backoff_delays = [5, 15, 45]
    for attempt in range(len(backoff_delays) + 1):
        try:
            result = await asyncio.to_thread(exa.search, query, num_results=10, type="neural")
            return [{"url": r.url, "title": r.title} for r in result.results]
        except Exception as e:
            error_str = str(e).lower()
            if "401" in error_str or "unauthorized" in error_str:
                raise RuntimeError("Exa API key is invalid") from e
            if attempt < len(backoff_delays) and ("429" in error_str or "500" in error_str or "503" in error_str):
                delay = backoff_delays[attempt]
                logger.warning("Exa search retry %d for '%s' after %ds: %s", attempt + 1, query, delay, e)
                await asyncio.sleep(delay)
                continue
            logger.error("Exa search failed for '%s': %s", query, e)
            return []


# --- Page reading (Jina) ---

async def read_page_jina(url: str, max_length: int = 15000) -> str | None:
    """Fetch clean Markdown of a web page via Jina Reader."""
    jina_url = f"https://r.jina.ai/{url}"
    headers: dict[str, str] = {"Accept": "text/plain"}
    if settings.jina_api_key:
        headers["Authorization"] = f"Bearer {settings.jina_api_key}"
    backoff_delays = [2, 5, 15]
    for attempt in range(len(backoff_delays) + 1):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(jina_url, headers=headers)
                if resp.status_code == 200:
                    return resp.text[:max_length]
                if resp.status_code == 429 and attempt < len(backoff_delays):
                    delay = backoff_delays[attempt]
                    logger.warning("Jina rate limited for %s, retry %d after %ds", url, attempt + 1, delay)
                    await asyncio.sleep(delay)
                    continue
                logger.warning("Jina returned %d for %s", resp.status_code, url)
                return None
        except Exception as e:
            logger.warning("Jina read failed for %s: %s", url, e)
            return None


# --- Title extraction (OpenAI) ---

_EXTRACT_PROMPT = (
    "Extract all board game titles mentioned in this text. "
    "Return a JSON array of strings. Only include actual board game names, "
    "not article titles or categories. If no board games are found, return []."
)


async def extract_titles_from_page(raw_text: str) -> list[str]:
    """Extract individual board game titles from page content using OpenAI."""
    if not settings.openai_api_key:
        return []
    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _EXTRACT_PROMPT},
                {"role": "user", "content": raw_text[:3000]},
            ],
            max_tokens=500,
            temperature=0,
        )
        content = resp.choices[0].message.content or "[]"
        # Strip markdown fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        titles = json.loads(content)
        if isinstance(titles, list):
            return [t.strip() for t in titles if isinstance(t, str) and t.strip()]
        return []
    except Exception as e:
        logger.warning("Title extraction failed: %s", e)
        return []


# --- Orchestration ---

async def discover_games(categories: list[str]) -> list[ScrapedGame]:
    """Discover board games by searching and reading pages."""
    queries = build_search_queries(categories)
    all_games: list[ScrapedGame] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()

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

            # Extract individual game titles from page content
            extracted = await extract_titles_from_page(raw_text)
            if not extracted:
                # Fallback: use search result title (only if it looks like a game name)
                fallback = clean_title(item.get("title", ""))
                if fallback and not is_listicle_title(fallback):
                    extracted = [fallback]

            for title in extracted:
                if is_listicle_title(title):
                    continue
                norm = title.lower().strip()
                if norm in seen_titles:
                    continue
                seen_titles.add(norm)
                all_games.append(ScrapedGame(
                    title=title,
                    source_url=url,
                    raw_text=raw_text,
                ))

    return all_games
