# Event Radar

Agent AI, który wyszukuje wydarzenia AI i startupowe w Polsce: warsztaty, meetupy, konferencje i hackathony. Docelowo będzie działał codziennie i wysyłał listę wydarzeń mailem.

**Status:** etap 1 z 7, czyli szkielet projektu i pierwszy agent z jednym narzędziem (wyszukiwarka Brave). Plan wszystkich etapów jest w [`CLAUDE.md`](CLAUDE.md).

## Czego potrzebujesz

- [uv](https://docs.astral.sh/uv/), czyli menedżer Pythona i bibliotek. Sam pobierze właściwą wersję Pythona (3.14).
- Klucz do modelu **Kimi** (Moonshot AI): <https://platform.moonshot.ai>
- Klucz do **Brave Search API**: <https://api-dashboard.search.brave.com>

## Instalacja

```bash
cp .env.example .env    # potem wpisz w .env swoje klucze
uv sync                 # instaluje Pythona i wszystkie biblioteki
```

Plik `.env` jest w `.gitignore`, więc klucze nigdy nie trafią do repozytorium. Jeśli zmienne `KIMI_API_KEY` i `BRAVE_API_KEY` są już ustawione w systemie, plik `.env` nie jest potrzebny.

## Uruchomienie

```bash
uv run event-radar "warsztaty AI Warszawa"
```

Bez zapytania agent użyje przykładowego „warsztaty AI Warszawa”. Program wypisuje każdy krok agenta, a na końcu listę wydarzeń:

```
Zapytanie: warsztaty AI Warszawa

[agent] Model postanowił użyć narzędzia web_search: {'query': 'warsztaty AI Warszawa 2026'}
[tools] Narzędzie web_search zwróciło: 10 wyników
[agent] Model nie potrzebuje już narzędzi i daje końcową odpowiedź.

Znalezione wydarzenia (1):

1. Warsztat AI w praktyce – KFK
   Data:   2026-11-16
   Miasto: Warszawa
   Link:   https://kfk.pl/szkolenia-ai
```

## Testy

```bash
uv run pytest
```

Testy nie łączą się z internetem i nic nie kosztują: zamiast prawdziwego modelu i wyszukiwarki używają podróbek.

## Jak to działa

Agent to graf LangGraph z dwoma węzłami:

```
START → agent ──(model prosi o narzędzie)──→ tools ──→ agent → ...
              └─(model daje odpowiedź)────→ KONIEC
```

1. **agent**: model Kimi K2.6 czyta pytanie i dotychczasowe wyniki. Decyduje, czy szukać dalej, czy już odpowiedzieć.
2. **tools**: uruchamia narzędzie `web_search` (Brave Search) i dopisuje wyniki do rozmowy.
3. Na końcu model zwraca listę JSON. Program sprawdza ją (biblioteka Pydantic) i wypisuje.

Agent może sięgnąć po narzędzie około 20 razy. Potem jest zatrzymywany z czytelnym komunikatem, żeby nie zapętlił się i nie generował kosztów.

## Struktura projektu

```
src/event_radar/
  config.py   # adresy usług, klucze ze zmiennych środowiskowych, ustawienia modelu Kimi
  tools.py    # narzędzie web_search (Brave Search)
  events.py   # opis wydarzenia (nazwa, data, miasto, link) i odczytywanie listy JSON
  agent.py    # graf LangGraph i instrukcja dla modelu
  cli.py      # polecenie terminalowe event-radar
tests/        # testy (bez internetu)
```

## Znane ograniczenia (do poprawy w kolejnych etapach)

- Agent widzi tylko krótkie opisy z wyników wyszukiwania, a nie całe strony. Dlatego często nie zna dokładnej daty i takie wydarzenia pomija. W etapie 2 dojdzie czytanie stron (Jina Reader).
- Integracja `ChatOpenAI` nie przekazuje modelowi jego wcześniejszego rozumowania (`reasoning_content`) między krokami. Szczegóły są w `CLAUDE.md`.
