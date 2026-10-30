# CLAUDE.md – kontekst projektu Event Radar

## Cel

Event Radar to agent AI, który codziennie wyszukuje wydarzenia AI i startupowe w Polsce (warsztaty, meetupy, konferencje, hackathony) i wysyła je mailem.

Właściciel projektu jest osobą nietechniczną i uczy się budowy agentów. Każdą decyzję tłumacz prostym językiem i wyjaśniaj, dlaczego wybrałeś dane rozwiązanie.

## Plan projektu (7 etapów)

1. **Szkielet i pierwszy agent** ✅ (obecny etap): projekt w uv, agent LangGraph z jednym narzędziem `web_search` (Brave), polecenie `event-radar`.
2. **Narzędzia:**
   - Exa (wyszukiwanie semantyczne),
   - Jina Reader (czytanie stron),
   - ustrukturyzowany wynik,
   - naprawa `reasoning_content` przez własną nakładkę na `ChatOpenAI` wzorowaną na `ChatDeepSeek`.
3. **Pamięć w Supabase:** wysłane eventy, obserwowane źródła, deduplikacja.
4. **Architektura wieloagentowa:** planista, równolegli researcherzy, weryfikator, redaktor.
5. **Mail:** sekcje, link „Dodaj do kalendarza”, oceny trafione/nietrafione.
6. **Codzienne uruchamianie przez GitHub Actions:** podgląd przebiegów, alert o błędach.
7. **Tydzień porównania z wersją w n8n.**

## Stos

- **Python 3.14** + **uv**.
  - Zależności dodawaj przez `uv add` (deweloperskie: `uv add --dev`), nie edytuj ich ręcznie w `pyproject.toml`.
- **LangGraph** jako framework agentowy.
  - Graf budujemy ręcznie (`StateGraph` + `ToolNode` + `tools_condition`), a nie gotowcem `create_agent`. Mechanika ma być widoczna.
- **Model: Kimi K2.6** przez API zgodne z OpenAI (`ChatOpenAI` z `langchain-openai`):
  - base URL: `https://api.moonshot.ai/v1`
  - model: `kimi-k2.6`
  - klucz: zmienna `KIMI_API_KEY`
  - **Dozwolone wyłącznie:** `temperature=1.0`, `top_p=0.95`, `presence_penalty=0`, `frequency_penalty=0`. Inne wartości powodują błąd. **Nie ustawiaj `n`.** Pilnuje tego `tests/test_config.py`.
  - `max_tokens=16000`, bo Kimi zaleca min. 16k w trybie myślenia. `ChatOpenAI` wysyła go jako `max_completion_tokens`, a Kimi to akceptuje.
  - W trybie myślenia `tool_choice` może być tylko `auto`/`none`. Nie da się więc wymusić wywołania narzędzia, np. przez `with_structured_output(method="function_calling")`.
- **Wyszukiwarka: Brave Search API:**
  - adres: `GET https://api.search.brave.com/res/v1/web/search`
  - nagłówek: `X-Subscription-Token` z wartością ze zmiennej `BRAVE_API_KEY`
  - wyniki są w `web.results`. Gdy nic nie znajdzie, pola `web` w ogóle nie ma.

## Zasady pracy

- **Kod i nazwy po angielsku; komentarze, docstringi i dokumentacja po polsku.** Instrukcje dla modelu (prompty) i opisy narzędzi też są po polsku.
- **Klucze wyłącznie w zmiennych środowiskowych.** Lokalnie trzymamy je w pliku `.env`, który jest w `.gitignore`. Nigdy nie wpisuj kluczy w kod ani do repozytorium. `.env.example` zawiera tylko puste nazwy zmiennych.
- **Małe kroki z testem po każdym.**
  - Testy mają działać bez internetu: podróbki zamiast prawdziwego API, np. `FakeModel` w `tests/test_agent.py`.
  - Prawdziwe uruchomienie (`uv run event-radar`) robimy na końcu etapu.

## Polecenia

```bash
uv sync                                     # instalacja
uv run pytest                               # testy (bez internetu)
uv run event-radar "warsztaty AI Warszawa"  # prawdziwe uruchomienie (płatne API)
```

## Struktura kodu

- `src/event_radar/config.py`: stałe (URL-e, model), `require_env()`, `get_llm()`.
- `src/event_radar/tools.py`: narzędzie `web_search`.
  - Błędy HTTP zwraca jako tekst, żeby agent mógł zareagować.
- `src/event_radar/events.py`: model `Event` (name, date, city, link) i `parse_events()`.
  - `parse_events()` wyciąga listę JSON z odpowiedzi modelu.
- `src/event_radar/agent.py`: `SYSTEM_PROMPT`, `build_graph()`, `MAX_TOOL_CALLS`, `RECURSION_LIMIT`.
- `src/event_radar/cli.py`: polecenie `event-radar`.
  - Wypisuje kroki grafu (`stream_mode="updates"`).
  - Przekroczenie limitu kroków (`GraphRecursionError`) zamienia na komunikat po polsku.

## Ustalenia techniczne i znane problemy

- **`reasoning_content` jest gubione (do naprawy w etapie 2).** `ChatOpenAI` nie odczytuje i nie odsyła pól spoza oficjalnego API OpenAI. Mówi o tym jego dokumentacja w kodzie. Kimi zaleca zachowywanie `reasoning_content` w historii przy wywołaniach narzędzi.
  - Sprawdzone 2026-10-29: bez tego pola Kimi **nie zwraca błędu**, więc agent działa. Model traci jednak swoje wcześniejsze rozumowanie między krokami.
  - Plan naprawy: własna podklasa `ChatOpenAI` wzorowana na `ChatDeepSeek` z `langchain-deepseek`.
    - Odczyt `reasoning_content` do `additional_kwargs`.
    - Odsyłanie tego pola w wiadomościach asystenta.
- **Limit kroków grafu:** `RECURSION_LIMIT = 2 * MAX_TOOL_CALLS + 2`.
  - Jeden cykl agent → narzędzie to 2 kroki, a końcowa odpowiedź to 1 krok. LangGraph potrzebuje jeszcze 1 kroku zapasu, żeby stwierdzić koniec grafu.
  - Efekt: 20 wyszukiwań + odpowiedź zawsze się mieści. Zapętlony agent zatrzymuje się po 21. wyszukiwaniu. Pilnuje tego `tests/test_agent.py`.
- **Dokumentacja Kimi** (`platform.moonshot.ai`, `platform.kimi.ai`) bywa niedostępna z sesji w chmurze, choć samo API (`api.moonshot.ai`) działa. Zachowanie API najlepiej sprawdzać krótkim, bezpośrednim wywołaniem.
