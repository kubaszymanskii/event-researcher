"""Narzędzia, z których może korzystać agent."""

import html
import re

import httpx
from langchain_core.tools import tool

from event_radar.config import BRAVE_SEARCH_URL, require_env

MAX_RESULTS = 10


@tool
def web_search(query: str) -> str:
    """Szuka w internecie (Brave Search) i zwraca wyniki: tytuł, link, opis i datę.

    Używaj krótkich, konkretnych zapytań, np. "warsztaty AI Warszawa listopad 2026".
    """
    try:
        response = httpx.get(
            BRAVE_SEARCH_URL,
            params={"q": query, "count": MAX_RESULTS, "country": "PL"},
            headers={
                "X-Subscription-Token": require_env("BRAVE_API_KEY"),
                "Accept": "application/json",
            },
            timeout=20,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        # Zwracamy błąd jako tekst, żeby agent mógł sam zdecydować, co dalej
        # (np. spróbować innego zapytania), zamiast przerywać cały program.
        return f"Błąd wyszukiwarki: {error}"
    return format_results(response.json())


def format_results(data: dict) -> str:
    """Zamienia odpowiedź Brave na czytelną listę tekstową dla modelu."""
    # Gdy Brave nic nie znajdzie, w odpowiedzi w ogóle nie ma pola "web".
    results = data.get("web", {}).get("results", [])
    if not results:
        return "Brak wyników dla tego zapytania."

    lines = []
    for number, result in enumerate(results, start=1):
        lines.append(f"{number}. {_clean(result.get('title', ''))}")
        lines.append(f"   Link: {result.get('url', '')}")
        if description := result.get("description"):
            lines.append(f"   Opis: {_clean(description)}")
        if age := result.get("age") or result.get("page_age"):
            lines.append(f"   Data publikacji: {age}")
    return "\n".join(lines)


def _clean(text: str) -> str:
    """Usuwa znaczniki HTML (np. <strong>) i zamienia encje typu &amp; na znaki."""
    return html.unescape(re.sub(r"<[^>]+>", "", text))
