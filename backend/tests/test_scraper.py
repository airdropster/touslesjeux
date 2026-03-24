# backend/tests/test_scraper.py
import pytest

from app.services.scraper import (
    ALLOWED_DOMAINS,
    is_allowed_url,
    build_search_queries,
    sanitize_html,
    ScrapedGame,
)


def test_allowed_domains_defined():
    assert "www.trictrac.net" in ALLOWED_DOMAINS
    assert "boardgamegeek.com" in ALLOWED_DOMAINS
    assert len(ALLOWED_DOMAINS) >= 6


def test_is_allowed_url_valid():
    # NOTE: is_allowed_url now calls _is_public_ip which does DNS resolution.
    # These tests require network connectivity. Mock _is_public_ip if running offline.
    assert is_allowed_url("https://www.trictrac.net/jeu/catan") is True
    assert is_allowed_url("https://boardgamegeek.com/boardgame/13/catan") is True


def test_is_allowed_url_invalid():
    assert is_allowed_url("https://evil.com/hack") is False
    assert is_allowed_url("http://127.0.0.1:8080/admin") is False
    assert is_allowed_url("file:///etc/passwd") is False


def test_build_search_queries():
    queries = build_search_queries(["des", "familial"])
    assert len(queries) >= 4
    assert any("des" in q for q in queries)
    assert any("familial" in q for q in queries)


def test_sanitize_html():
    html = '<div><script>alert("x")</script><p>Catan is a game</p></div>'
    text = sanitize_html(html)
    assert "alert" not in text
    assert "Catan is a game" in text


def test_sanitize_html_max_length():
    html = "<p>" + "x" * 20000 + "</p>"
    text = sanitize_html(html, max_length=15000)
    assert len(text) <= 15000


def test_scraped_game_dataclass():
    game = ScrapedGame(title="Catan", source_url="https://www.trictrac.net/jeu/catan")
    assert game.title == "Catan"
    assert game.year is None
