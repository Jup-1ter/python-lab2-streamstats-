from datetime import datetime
from pathlib import Path
from typing import Any

from streamstats.constants import ERROR_LEVELS, LEVELS, TOP_SOURCES_LIMIT
from streamstats.errors import (
    InvalidEventError,
    StreamStatsError,
    UnsupportedFormatError,
)
from streamstats.models import Event, validate_event
from streamstats.parsers import parse_csv, parse_jsonl


class Statistics:
    """Класс для сбора статистики."""

    def __init__(self) -> None:
        """Инициализация"""
        self.total = 0
        self.levels = {level: 0 for level in LEVELS}
        self.sources: dict[str, int] = {}
        self.error_sources: dict[str, int] = {}
        self.first_timestamp: str | None = None
        self.last_timestamp: str | None = None
        self.first_moment: datetime | None = None
        self.last_moment: datetime | None = None
        self.skipped = 0

    def add(self, event: Event) -> None:
        """Добавить событие к статистике."""

        self.total += 1
        self.levels[event.level] += 1
        self.sources[event.source] = self.sources.get(event.source, 0) + 1
        if event.level in ERROR_LEVELS:
            self.error_sources[event.source] = self.error_sources.get(event.source, 0) + 1
        if self.first_moment is None or event.moment < self.first_moment:
            self.first_moment = event.moment
            self.first_timestamp = event.timestamp
        if self.last_moment is None or event.moment > self.last_moment:
            self.last_moment = event.moment
            self.last_timestamp = event.timestamp

    def to_dict(self) -> dict[str, Any]:
        """Представить статистику в виде словаря"""
        top_sources = sorted(
            self.error_sources.items(), key=lambda item: (-item[1], item[0])
        )[:TOP_SOURCES_LIMIT]
        return {
            "total_events": self.total,
            "events_per_level": self.levels,
            "events_per_source": self.sources,
            "top_error_sources": [
                {"source": source, "count": count} for source, count in top_sources
            ],
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "skipped_invalid_lines": self.skipped,
        }


def process_files(paths: list[str], input_format: str, skip_invalid: bool) -> Statistics:
    """Последовательная обработка файлов и сбор общей статистики."""

    if input_format not in ("csv", "jsonl"):
        raise UnsupportedFormatError(f"Неподдерживаемый формат: {input_format}")

    stats = Statistics()
    parser = parse_csv if input_format == "csv" else parse_jsonl
    for filename in paths:
        path = Path(filename)
        try:
            for line_number, record in parser(path):
                try:
                    if isinstance(record, StreamStatsError):
                        raise record
                    stats.add(validate_event(record))
                except InvalidEventError as error:
                    message = f"{filename}:{line_number}: {error}"
                    if not skip_invalid:
                        raise InvalidEventError(message) from error
                    import logging

                    logging.getLogger("streamstats").warning("Пропуск некорректной строки %s", message)
                    stats.skipped += 1
        except (OSError, UnicodeError) as error:
            from streamstats.errors import CLIConfigurationError

            raise CLIConfigurationError(f"Не удалось прочитать файл {filename}: {error}") from error
    return stats
