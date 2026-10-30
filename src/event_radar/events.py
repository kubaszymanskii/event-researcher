"""Model danych wydarzenia i odczytywanie listy wydarzeń z odpowiedzi agenta."""

from pydantic import BaseModel, TypeAdapter, ValidationError


class Event(BaseModel):
    """Jedno wydarzenie znalezione przez agenta."""

    name: str
    # Tekst, a nie typ daty, bo strony często podają daty niepełne, np. "listopad 2026".
    date: str
    city: str
    link: str


class EventParseError(ValueError):
    """Odpowiedź agenta nie zawiera poprawnej listy wydarzeń."""


_EVENT_LIST = TypeAdapter(list[Event])


def parse_events(text: str) -> list[Event]:
    """Wyciąga z odpowiedzi agenta listę JSON i sprawdza, czy każde wydarzenie ma wymagane pola.

    Model czasem otacza JSON blokiem ```json ... ``` albo dopisuje zdanie wstępu,
    dlatego bierzemy fragment od pierwszego "[" do ostatniego "]".
    """
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end < start:
        raise EventParseError("W odpowiedzi agenta nie ma listy JSON.")
    try:
        return _EVENT_LIST.validate_json(text[start : end + 1])
    except ValidationError as error:
        raise EventParseError(f"Lista wydarzeń ma niepoprawny format: {error}") from error
