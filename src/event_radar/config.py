"""Konfiguracja: adresy usług, klucze ze zmiennych środowiskowych i ustawienia modelu Kimi."""

import os

from langchain_openai import ChatOpenAI

KIMI_BASE_URL = "https://api.moonshot.ai/v1"
KIMI_MODEL = "kimi-k2.6"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


class MissingApiKeyError(RuntimeError):
    """Brakuje klucza API w zmiennych środowiskowych."""


def require_env(name: str) -> str:
    """Zwraca wartość zmiennej środowiskowej albo zgłasza czytelny błąd, gdy jej brakuje."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise MissingApiKeyError(
            f"Brakuje zmiennej środowiskowej {name}. "
            "Skopiuj .env.example jako .env i wpisz w nim swój klucz."
        )
    return value


def get_llm() -> ChatOpenAI:
    """Tworzy klienta modelu Kimi K2.6 przez API zgodne z OpenAI.

    Kimi K2.6 przyjmuje tylko poniższe wartości parametrów – inne powodują błąd.
    Parametru `n` celowo nie ustawiamy (biblioteka wtedy go nie wysyła).
    """
    return ChatOpenAI(
        model=KIMI_MODEL,
        base_url=KIMI_BASE_URL,
        api_key=require_env("KIMI_API_KEY"),
        temperature=1.0,
        top_p=0.95,
        presence_penalty=0,
        frequency_penalty=0,
        # Kimi zaleca min. 16 000 tokenów w trybie myślenia,
        # żeby rozumowanie i odpowiedź nie zostały ucięte.
        max_tokens=16000,
    )
