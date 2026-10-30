"""Testy odczytywania listy wydarzeń z odpowiedzi agenta."""

import pytest

from event_radar.events import Event, EventParseError, parse_events

EVENT_JSON = (
    '[{"name": "AI Meetup", "date": "2026-11-12", "city": "Warszawa", '
    '"link": "https://example.com/meetup"}]'
)
EXPECTED = [
    Event(name="AI Meetup", date="2026-11-12", city="Warszawa", link="https://example.com/meetup")
]


def test_plain_json():
    assert parse_events(EVENT_JSON) == EXPECTED


def test_json_in_code_block_with_intro():
    text = f"Oto znalezione wydarzenia:\n```json\n{EVENT_JSON}\n```"
    assert parse_events(text) == EXPECTED


def test_empty_list_is_valid():
    assert parse_events("[]") == []


def test_missing_field_raises():
    with pytest.raises(EventParseError):
        parse_events('[{"name": "AI Meetup", "date": "2026-11-12"}]')


def test_text_without_json_raises():
    with pytest.raises(EventParseError):
        parse_events("Nie znalazłem żadnych wydarzeń.")
