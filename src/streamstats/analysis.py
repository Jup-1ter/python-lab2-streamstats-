from pathlib import Path
from typing import Any

from streamstats.constants import ERROR_LEVELS, LEVELS, TOP_SOURCES_LIMIT
from streamstats.models import Event, validate_event
from streamstats.parsers import parse_csv, parse_jsonl


class Statistics:
    """Класс для сбора статистики."""

    def __init__(self) -> None:
        self.total = 0
        self.levels = {level: 0 for level in LEVELS}
        self.sources: dict[str, int] = {}
        self.error_sources: dict[str, int] = {}
        self.first_timestamp: str | None = None
        self.last_timestamp: str | None = None

    def add(self, event: Event) -> None:
        self.total += 1
        self.levels[event.level] += 1
        self.sources[event.source] = self.sources.get(event.source, 0) + 1
        if event.level in ERROR_LEVELS:
            self.error_sources[event.source] = self.error_sources.get(event.source, 0) + 1
        if self.first_timestamp is None or event.timestamp < self.first_timestamp:
            self.first_timestamp = event.timestamp
        if self.last_timestamp is None or event.timestamp > self.last_timestamp:
            self.last_timestamp = event.timestamp

    def to_dict(self) -> dict[str, Any]:
        top_sources = sorted(self.error_sources.items(), key=lambda item: (-item[1], item[0]))[:TOP_SOURCES_LIMIT]
        return {
            "total_events": self.total,
            "events_per_level": self.levels,
            "events_per_source": self.sources,
            "top_error_sources": [{"source": source, "count": count} for source, count in top_sources],
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "skipped_invalid_lines": 0,
        }


def process_files(paths: list[str], input_format: str, skip_invalid: bool = False) -> Statistics:
    if input_format not in ("csv", "jsonl"):
        from streamstats.errors import UnsupportedFormatError
        raise UnsupportedFormatError(f"Неподдерживаемый формат: {input_format}")
    stats = Statistics()
    parser = parse_csv if input_format == "csv" else parse_jsonl
    for filename in paths:
        for _, record in parser(Path(filename)):
            stats.add(validate_event(record))
    return stats
