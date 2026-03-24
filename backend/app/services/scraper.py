# backend/app/services/scraper.py
import asyncio
import ipaddress
import logging
import socket
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_DOMAINS = frozenset([
    "www.trictrac.net",
    "www.philibertnet.com",
    "boardgamegeek.com",
    "www.espritjeu.com",
    "www.ludum.fr",
    "www.game-blog.fr",
])

USER_AGENT = "TousLesJeux-Bot/1.0"
THROTTLE_SECONDS = 2.0


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


def _is_public_ip(hostname: str) -> bool:
    """Resolve hostname and verify IP is not private/loopback (SSRF prevention)."""
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for family, _, _, _, sockaddr in addr_info:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                return False
        return True
    except (socket.gaierror, ValueError):
        return False


def is_allowed_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname or ""
        if hostname not in ALLOWED_DOMAINS:
            return False
        return _is_public_ip(hostname)
    except Exception:
        return False


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


def sanitize_html(html: str, max_length: int = 15000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "iframe", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return text[:max_length]


async def search_google_cse(query: str) -> list[dict]:
    if not settings.google_cse_api_key or not settings.google_cse_cx:
        logger.warning("Google CSE API key or CX not configured")
        return []
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": settings.google_cse_api_key,
        "cx": settings.google_cse_cx,
        "q": query,
        "num": 10,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        if resp.status_code == 403:
            logger.error("Google CSE quota exceeded")
            return []
        if resp.status_code == 401:
            raise RuntimeError("Google CSE API key is invalid")
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])


_robots_cache: dict[str, RobotFileParser] = {}


async def _check_robots(url: str) -> bool:
    """Check if URL is allowed by robots.txt. Caches per origin."""
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.hostname}"
    if origin not in _robots_cache:
        rp = RobotFileParser()
        robots_url = f"{origin}/robots.txt"
        try:
            async with httpx.AsyncClient(timeout=5.0, headers={"User-Agent": USER_AGENT}) as client:
                resp = await client.get(robots_url)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp.allow_all = True
        except Exception:
            rp.allow_all = True
        _robots_cache[origin] = rp
    return _robots_cache[origin].can_fetch(USER_AGENT, url)


async def scrape_page(url: str) -> str | None:
    if not is_allowed_url(url):
        return None
    if not await _check_robots(url):
        logger.info("Blocked by robots.txt: %s", url)
        return None
    try:
        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=False,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            return resp.text
    except Exception as e:
        logger.warning("Scraping failed for %s: %s", url, e)
        return None


def extract_game_titles_from_html(html: str, source_url: str) -> list[ScrapedGame]:
    """Generic extractor: finds game-like titles from page content."""
    text = sanitize_html(html)
    return [ScrapedGame(title="", source_url=source_url, raw_text=text)]


async def discover_games(categories: list[str]) -> list[ScrapedGame]:
    queries = build_search_queries(categories)
    all_games: list[ScrapedGame] = []
    seen_urls: set[str] = set()

    for query in queries:
        try:
            results = await search_google_cse(query)
        except RuntimeError:
            raise
        except Exception as e:
            logger.error("Search failed for '%s': %s", query, e)
            continue

        for item in results:
            url = item.get("link", "")
            if url in seen_urls or not is_allowed_url(url):
                continue
            seen_urls.add(url)

            await asyncio.sleep(THROTTLE_SECONDS)
            html = await scrape_page(url)
            if not html:
                continue

            games = extract_game_titles_from_html(html, url)
            for g in games:
                if not g.title:
                    g.title = item.get("title", "").split(" - ")[0].split(" | ")[0].strip()
                if g.title:
                    all_games.append(g)

    return all_games
