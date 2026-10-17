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
