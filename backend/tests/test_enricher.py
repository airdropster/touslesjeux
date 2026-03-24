# backend/tests/test_enricher.py
import pytest

from app.services.enricher import build_user_prompt, SYSTEM_PROMPT


def test_system_prompt_exists():
    assert "expert" in SYSTEM_PROMPT.lower() or "jeux" in SYSTEM_PROMPT.lower()
    assert "1800" in SYSTEM_PROMPT
    assert "<game_description>" in SYSTEM_PROMPT


def test_build_user_prompt():
    prompt = build_user_prompt("Catan", 1995, "Some scraped text about Catan")
    assert "Catan" in prompt
    assert "1995" in prompt
    assert "<game_description>" in prompt
    assert "Some scraped text" in prompt


def test_build_user_prompt_no_year():
    prompt = build_user_prompt("Catan", None, "Some text")
    assert "inconnue" in prompt
