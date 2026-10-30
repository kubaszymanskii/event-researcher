"""Testy grafu agenta – z udawanym modelem, bez internetu i bez kosztów."""

import itertools

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.errors import GraphRecursionError

from event_radar.agent import MAX_TOOL_CALLS, build_graph


class FakeModel(GenericFakeChatModel):
    """Udawany model, który odtwarza przygotowane wcześniej odpowiedzi."""

    def bind_tools(self, tools, **kwargs):
        return self


def search_request(number: int) -> AIMessage:
    """Odpowiedź modelu, w której prosi o użycie narzędzia."""
    return AIMessage(
        content="",
        tool_calls=[{"name": "fake_search", "args": {"query": "AI"}, "id": f"call_{number}"}],
    )


def make_fake_search(calls: list):
    @tool
    def fake_search(query: str) -> str:
        """Udawane wyszukiwanie."""
        calls.append(query)
        return "Brak wyników dla tego zapytania."

    return fake_search


def test_graph_has_agent_and_tools_nodes():
    graph = build_graph(llm=FakeModel(messages=iter([])), tools=[make_fake_search([])])
    assert {"agent", "tools"} <= set(graph.get_graph().nodes)


def test_agent_can_make_max_tool_calls_and_answer():
    calls = []
    answers = [search_request(i) for i in range(MAX_TOOL_CALLS)] + [AIMessage(content="[]")]
    graph = build_graph(llm=FakeModel(messages=iter(answers)), tools=[make_fake_search(calls)])

    result = graph.invoke({"messages": [HumanMessage("AI")]})

    assert len(calls) == MAX_TOOL_CALLS
    assert sum(isinstance(m, ToolMessage) for m in result["messages"]) == MAX_TOOL_CALLS
    assert result["messages"][-1].content == "[]"


def test_agent_is_stopped_after_exceeding_limit():
    calls = []
    endless = (search_request(i) for i in itertools.count())
    graph = build_graph(llm=FakeModel(messages=endless), tools=[make_fake_search(calls)])

    with pytest.raises(GraphRecursionError):
        graph.invoke({"messages": [HumanMessage("AI")]})
    # Zapas na zakończenie grafu sprawia, że zapętlony agent zdąży wykonać jedno wyszukiwanie więcej.
    assert len(calls) == MAX_TOOL_CALLS + 1
