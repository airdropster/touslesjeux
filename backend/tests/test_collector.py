# backend/tests/test_collector.py
import pytest

from app.services.collector import SSEEvent


def test_sse_event_progress():
    event = SSEEvent.progress(processed=5, total=100, skipped=1, current_game="Catan")
    assert event.event == "progress"
    assert event.data["processed"] == 5
    assert event.data["current_game"] == "Catan"


def test_sse_event_game_added():
    event = SSEEvent.game_added(game_id=42, title="Catan")
    assert event.event == "game_added"
    assert event.data["id"] == 42


def test_sse_event_completed():
    event = SSEEvent.completed(processed=97, skipped=3, failed=0)
    assert event.event == "completed"
    assert event.data["processed"] == 97
