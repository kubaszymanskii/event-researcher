"""Testy narzędzia web_search – bez internetu, z podstawioną odpowiedzią Brave."""

import httpx

from event_radar import tools


def fake_get(status_code, body, calls):
    """Tworzy podróbkę httpx.get, która zapamiętuje wywołanie i zwraca podaną odpowiedź."""

    def _get(url, params, headers, timeout):
        calls.append({"url": url, "params": params, "headers": headers})
        return httpx.Response(status_code, json=body, request=httpx.Request("GET", url))

    return _get


def test_returns_formatted_results(monkeypatch):
    monkeypatch.setenv("BRAVE_API_KEY", "brave-test-key")
    calls = []
    body = {
        "web": {
            "results": [
                {
                    "title": "Warsztaty <strong>AI</strong> &amp; ML",
                    "url": "https://example.com/ai",
                    "description": "Praktyczne <strong>warsztaty</strong> w Warszawie",
                    "age": "3 days ago",
                }
            ]
        }
    }
    monkeypatch.setattr(tools.httpx, "get", fake_get(200, body, calls))

    output = tools.web_search.invoke({"query": "warsztaty AI Warszawa"})

    assert "1. Warsztaty AI & ML" in output
    assert "Link: https://example.com/ai" in output
    assert "Opis: Praktyczne warsztaty w Warszawie" in output
    assert "Data publikacji: 3 days ago" in output
    assert calls[0]["params"]["q"] == "warsztaty AI Warszawa"
    assert calls[0]["headers"]["X-Subscription-Token"] == "brave-test-key"


def test_missing_web_field_means_no_results(monkeypatch):
    monkeypatch.setenv("BRAVE_API_KEY", "brave-test-key")
    monkeypatch.setattr(tools.httpx, "get", fake_get(200, {"type": "search"}, []))

    assert tools.web_search.invoke({"query": "xyz"}) == "Brak wyników dla tego zapytania."


def test_http_error_is_returned_as_text(monkeypatch):
    monkeypatch.setenv("BRAVE_API_KEY", "brave-test-key")
    monkeypatch.setattr(tools.httpx, "get", fake_get(429, {}, []))

    assert tools.web_search.invoke({"query": "xyz"}).startswith("Błąd wyszukiwarki:")
