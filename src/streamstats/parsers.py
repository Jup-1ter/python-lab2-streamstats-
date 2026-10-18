import csv
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from streamstats.errors import InvalidEventError

ParsedLine = tuple[int, dict[str, Any] | InvalidEventError]


def parse_jsonl(path: Path) -> Iterator[ParsedLine]:
    """Возврат непустых JSONL записей или ошибок."""
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise InvalidEventError("Некорректный JSONL объект")
                yield line_number, value
            except json.JSONDecodeError as error:
                yield line_number, InvalidEventError(f"Синтаксическая ошибка JSON: {error.msg}")
            except InvalidEventError as error:
                yield line_number, error


def parse_csv(path: Path) -> Iterator[ParsedLine]:
    """Возврат CSV записей с их номерами."""
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return
        previous_line = reader.line_num
        while True:
            start_line = previous_line + 1
            try:
                row = next(reader)
            except StopIteration:
                return
            except csv.Error as error:
                yield start_line, InvalidEventError(f"Некорректный CSV: {error}")
                previous_line = reader.line_num
                continue
            previous_line = reader.line_num
            if None in row:
                yield start_line, InvalidEventError("В CSV строке больше ячеек, чем в заголовек")
            elif any(value is None for value in row.values()):
                yield start_line, InvalidEventError("В CSV строке меньше ячеек, чем в заголовек")
            else:
                yield start_line, {key: value for key, value in row.items() if key is not None}
