from datetime import datetime
from typing import Any

from streamstats.constants import LEVELS
from streamstats.errors import InvalidEventError, InvalidTimestampError


class Event:
    """Класс модели события."""

    def __init__(self, timestamp: str, level: str, source: str, message: str) -> None:
        self.timestamp = timestamp
        self.level = level
        self.source = source
        self.message = message
        try:
            self.moment = datetime.fromisoformat(timestamp)
        except ValueError as error:
            raise InvalidTimestampError(f"Некорректная временная метка: {timestamp!r}") from error


def validate_event(record: dict[str, Any]) -> Event:
    """Валидация словаря события."""
    required = ("timestamp", "level", "source", "message")
    for field in required:
        if field not in record:
            raise InvalidEventError(f"Отсутствует обязательное поле: {field}")
        if not isinstance(record[field], str):
            raise InvalidEventError(f"Поле {field} должно быть строкой")
    if record["level"] not in LEVELS:
        raise InvalidEventError(f"Некорректный уровень важности: {record['level']!r}")
    if not record["source"]:
        raise InvalidEventError("Поле источника не может быть пустым")
    return Event(record["timestamp"], record["level"], record["source"], record["message"])
