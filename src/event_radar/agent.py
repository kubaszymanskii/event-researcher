"""Agent Event Radar zbudowany jako graf LangGraph.

Graf ma dwa węzły i krąży między nimi, dopóki model chce używać narzędzi:

    START → agent ──(model prosi o narzędzie)──→ tools ──→ agent → ...
                  └─(model daje odpowiedź)────→ END
"""

from datetime import date

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from event_radar.config import get_llm
from event_radar.tools import web_search

# Ile razy agent może sięgnąć po narzędzia, zanim go zatrzymamy (ochrona przed pętlą i kosztami).
# Jeśli model poprosi o kilka wyszukiwań naraz, liczą się jako jedno sięgnięcie – stąd „około”.
MAX_TOOL_CALLS = 20
# Jeden cykl agent → narzędzie to 2 kroki grafu, a końcowa odpowiedź agenta to 1 krok.
# LangGraph potrzebuje jeszcze 1 kroku zapasu, żeby stwierdzić, że graf się zakończył.
# Dzięki temu agent zdąży wykonać 20 wyszukiwań i odpowiedzieć, a agent, który się zapętli,
# zostanie zatrzymany najpóźniej po 21. wyszukiwaniu. Sprawdzone w tests/test_agent.py.
RECURSION_LIMIT = 2 * MAX_TOOL_CALLS + 2

SYSTEM_PROMPT = """Jesteś asystentem, który wyszukuje wydarzenia AI i startupowe w Polsce.
Dzisiejsza data: {today}.

Jak pracujesz:
1. Używaj narzędzia web_search, żeby znaleźć wydarzenia pasujące do prośby użytkownika.
   Możesz wyszukiwać kilka razy, z różnymi zapytaniami (np. dodając miesiąc lub rok),
   ale zwykle wystarczą 2–4 wyszukiwania.
2. Uwzględniaj tylko konkretne wydarzenia (warsztaty, meetupy, konferencje, hackathony itp.),
   które odbywają się dziś lub później. Pomijaj stałe oferty kursów bez konkretnego terminu.
3. Nie wymyślaj danych. Jeśli w wynikach nie ma daty albo miasta, wpisz "nieznana" / "nieznane".

Odpowiedź końcowa to wyłącznie lista JSON, bez żadnego innego tekstu, w formacie:
[{{"name": "nazwa wydarzenia", "date": "RRRR-MM-DD", "city": "miasto", "link": "https://..."}}]
Jeśli nic nie znajdziesz, zwróć [].
"""


def build_graph(
    llm: BaseChatModel | None = None, tools: list[BaseTool] | None = None
) -> CompiledStateGraph:
    """Składa graf agenta. Model i narzędzia można podmienić (przydaje się w testach)."""
    llm = llm or get_llm()
    tools = tools or [web_search]
    # bind_tools dołącza do każdego zapytania opis narzędzi (nazwa, opis, parametry),
    # dzięki czemu model wie, że może o nie poprosić.
    llm_with_tools = llm.bind_tools(tools)

    def agent(state: MessagesState) -> dict:
        """Węzeł „agent”: model czyta całą dotychczasową rozmowę i decyduje, co dalej."""
        system = SystemMessage(SYSTEM_PROMPT.format(today=date.today().isoformat()))
        response = llm_with_tools.invoke([system, *state["messages"]])
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools))  # węzeł „tools”: uruchamia narzędzia
    builder.add_edge(START, "agent")
    # Krawędź warunkowa: jeśli model poprosił o narzędzie → "tools", w przeciwnym razie → koniec.
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder.compile().with_config(recursion_limit=RECURSION_LIMIT)
