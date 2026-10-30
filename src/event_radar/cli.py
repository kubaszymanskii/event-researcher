"""Polecenie terminalowe: uv run event-radar "zapytanie"."""

import argparse
import re
import sys

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.errors import GraphRecursionError
from langgraph.graph.state import CompiledStateGraph

from event_radar.agent import MAX_TOOL_CALLS, build_graph
from event_radar.config import MissingApiKeyError, require_env
from event_radar.events import Event, EventParseError, parse_events

DEFAULT_QUERY = "warsztaty AI Warszawa"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="event-radar", description="Wyszukuje wydarzenia AI i startupowe w Polsce."
    )
    parser.add_argument(
        "query", nargs="?", default=DEFAULT_QUERY, help=f'zapytanie (domyślnie: "{DEFAULT_QUERY}")'
    )
    args = parser.parse_args(argv)

    # Wczytuje plik .env, jeśli istnieje. Zmienne ustawione w systemie mają pierwszeństwo.
    load_dotenv()
    try:
        # Sprawdzamy klucz Brave od razu, żeby nie płacić za model, gdy wyszukiwarka i tak nie zadziała.
        require_env("BRAVE_API_KEY")
        final_answer = run_agent(build_graph(), args.query)
    except MissingApiKeyError as error:
        print(f"Błąd konfiguracji: {error}", file=sys.stderr)
        return 1
    except GraphRecursionError:
        print(
            f"Agent przekroczył limit około {MAX_TOOL_CALLS} wyszukiwań i został zatrzymany. "
            "Spróbuj bardziej konkretnego zapytania.",
            file=sys.stderr,
        )
        return 1

    try:
        events = parse_events(final_answer)
    except EventParseError as error:
        print(f"\nNie udało się odczytać listy wydarzeń ({error}).", file=sys.stderr)
        print(f"Surowa odpowiedź agenta:\n{final_answer}", file=sys.stderr)
        return 1
    print_events(events)
    return 0


def run_agent(graph: CompiledStateGraph, query: str) -> str:
    """Uruchamia agenta, wypisuje każdy krok grafu i zwraca końcową odpowiedź modelu."""
    print(f"Zapytanie: {query}\n")
    final_answer = ""
    # stream_mode="updates" oddaje wynik po każdym kroku grafu: {nazwa_węzła: zmiany_w_stanie}.
    for update in graph.stream({"messages": [HumanMessage(query)]}, stream_mode="updates"):
        for node, changes in update.items():
            for message in changes["messages"]:
                describe_step(node, message)
                if isinstance(message, AIMessage) and not message.tool_calls:
                    final_answer = message.text
    return final_answer


def describe_step(node: str, message) -> None:
    """Wypisuje po polsku, co wydarzyło się w danym kroku."""
    if isinstance(message, AIMessage) and message.tool_calls:
        for call in message.tool_calls:
            print(f"[{node}] Model postanowił użyć narzędzia {call['name']}: {call['args']}")
    elif isinstance(message, AIMessage):
        print(f"[{node}] Model nie potrzebuje już narzędzi i daje końcową odpowiedź.")
    elif isinstance(message, ToolMessage):
        content = str(message.content)
        found = len(re.findall(r"^\d+\. ", content, flags=re.MULTILINE))
        summary = f"{found} wyników" if found else content.splitlines()[0]
        print(f"[{node}] Narzędzie {message.name} zwróciło: {summary}")


def print_events(events: list[Event]) -> None:
    if not events:
        print("\nAgent nie znalazł pasujących wydarzeń.")
        return
    print(f"\nZnalezione wydarzenia ({len(events)}):\n")
    for number, event in enumerate(events, start=1):
        print(f"{number}. {event.name}")
        print(f"   Data:   {event.date}")
        print(f"   Miasto: {event.city}")
        print(f"   Link:   {event.link}\n")
