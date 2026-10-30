"""Testy polecenia terminalowego."""

import itertools

from langchain_core.messages import AIMessage

from event_radar import cli
from event_radar.agent import build_graph
from tests.test_agent import FakeModel, make_fake_search, search_request


def test_exceeded_limit_prints_polish_message_instead_of_traceback(monkeypatch, capsys):
    monkeypatch.setenv("BRAVE_API_KEY", "brave-test-key")
    endless = (search_request(i) for i in itertools.count())
    graph = build_graph(llm=FakeModel(messages=endless), tools=[make_fake_search([])])
    monkeypatch.setattr(cli, "build_graph", lambda: graph)

    exit_code = cli.main(["warsztaty AI Warszawa"])

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "przekroczył limit około 20 wyszukiwań" in err
    assert "Traceback" not in err


def test_events_are_printed(monkeypatch, capsys):
    monkeypatch.setenv("BRAVE_API_KEY", "brave-test-key")
    answer = AIMessage(
        content='[{"name": "AI Meetup", "date": "2026-11-12", "city": "Warszawa", '
        '"link": "https://example.com"}]'
    )
    graph = build_graph(llm=FakeModel(messages=iter([answer])), tools=[make_fake_search([])])
    monkeypatch.setattr(cli, "build_graph", lambda: graph)

    assert cli.main([]) == 0
    out = capsys.readouterr().out
    assert "Zapytanie: warsztaty AI Warszawa" in out
    assert "1. AI Meetup" in out
    assert "Miasto: Warszawa" in out
