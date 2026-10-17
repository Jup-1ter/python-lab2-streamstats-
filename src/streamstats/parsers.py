import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

ParsedLine = tuple[int, dict[str, Any]]


def parse_jsonl(path: Path) -> Iterator[ParsedLine]:
    """Чтение объектов из JSONL."""
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if isinstance(value, dict):
                yield line_number, value


import csv


def parse_csv(path: Path) -> Iterator[ParsedLine]:
    """Чтение CSV записей с заголовком."""
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for line_number, row in enumerate(reader, start=2):
            yield line_number, {key: value for key, value in row.items() if key is not None and value is not None}
