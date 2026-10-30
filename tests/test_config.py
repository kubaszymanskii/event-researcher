"""Testy konfiguracji modelu – pilnują ograniczeń Kimi K2.6."""

import pytest
from langchain_core.messages import HumanMessage

from event_radar.config import MissingApiKeyError, get_llm


def test_llm_sends_only_parameters_allowed_by_kimi(monkeypatch):
    monkeypatch.setenv("KIMI_API_KEY", "test-key")
    llm = get_llm()

    # Sprawdzamy dokładnie to, co poleci do API.
    payload = llm._get_request_payload([HumanMessage("cześć")])

    assert payload["model"] == "kimi-k2.6"
    assert payload["temperature"] == 1.0
    assert payload["top_p"] == 0.95
    assert payload["presence_penalty"] == 0
    assert payload["frequency_penalty"] == 0
    assert "n" not in payload
    assert str(llm.openai_api_base) == "https://api.moonshot.ai/v1"


def test_missing_key_gives_clear_error(monkeypatch):
    monkeypatch.delenv("KIMI_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError, match="KIMI_API_KEY"):
        get_llm()
