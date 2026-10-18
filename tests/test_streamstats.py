import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from streamstats.analysis import Statistics, process_files
from streamstats.errors import InvalidEventError
from streamstats.models import validate_event
from streamstats.parsers import parse_csv, parse_jsonl


def test_jsonl_parser_reads_objects_and_ignores_blank_lines(tmp_path: Path) -> None:
    """Чтение JSONL событий с сохранением номеров при наличии пустых строк."""
    path = tmp_path / "events.jsonl"
    path.write_text(
        '\n{"timestamp":"2026-01-01T00:00:00Z","level":"INFO","source":"s","message":"m"}\n',
        encoding="utf-8",
    )
    rows = list(parse_jsonl(path))
    assert len(rows) == 1
    assert rows[0][0] == 2
    assert isinstance(rows[0][1], dict)


def test_csv_parser_reads_header_records(tmp_path: Path) -> None:
    """чтение CSV событий с заголовком."""
    path = tmp_path / "events.csv"
    path.write_text("timestamp,level,source,message\nt,INFO,s,m\n", encoding="utf-8")
    rows = list(parse_csv(path))
    assert rows == [(2, {"timestamp": "t", "level": "INFO", "source": "s", "message": "m"})]


def test_empty_file_produces_empty_report(tmp_path: Path) -> None:
    """Принятие пустого файла"""
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    report = process_files([str(path)], "jsonl", False).to_dict()
    assert report["total_events"] == 0
    assert report["first_timestamp"] is None
    assert report["skipped_invalid_lines"] == 0
    assert set(report["events_per_level"]) == {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def test_invalid_json_stops_by_default(tmp_path: Path) -> None:
    """Выбрасывание исключения для некорректного JSONL."""
    path = tmp_path / "broken.jsonl"
    path.write_text('{"timestamp":}\n', encoding="utf-8")
    with pytest.raises(InvalidEventError, match=r"broken.jsonl:1"):
        process_files([str(path)], "jsonl", False)


def test_skip_invalid_counts_later_valid_records(tmp_path: Path) -> None:
    """Пропуск некорректных строк и продолжение обработки"""
    path = tmp_path / "mixed.jsonl"
    valid = {"timestamp": "2026-01-01T00:00:00Z", "level": "INFO", "source": "s", "message": "ok"}
    path.write_text("bad json\n" + json.dumps(valid) + "\n", encoding="utf-8")
    report = process_files([str(path)], "jsonl", True).to_dict()
    assert report["total_events"] == 1
    assert report["skipped_invalid_lines"] == 1


def test_multiple_files_merge(tmp_path: Path) -> None:
    """Объединение статистики по нескольким файлам."""
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    first_event = {
        "timestamp": "2026-01-01T00:00:00Z", "level": "ERROR",
        "source": "служба", "message": "ошибка",
    }
    first.write_text(json.dumps(first_event, ensure_ascii=False) + "\n", encoding="utf-8")
    second_event = {
        "timestamp": "2026-01-02T00:00:00Z", "level": "INFO",
        "source": "служба", "message": "готово",
    }
    second.write_text(json.dumps(second_event, ensure_ascii=False) + "\n", encoding="utf-8")
    report = process_files([str(first), str(second)], "jsonl", False).to_dict()
    assert report["total_events"] == 2
    assert report["events_per_source"] == {"служба": 2}
    assert report["top_error_sources"] == [{"source": "служба", "count": 1}]


def test_timestamp_comparison_uses_moments() -> None:
    """Сравнение временных меток по моменту времени."""
    early = validate_event(
        {"timestamp": "2026-10-07T12:00:00+03:00", "level": "INFO", "source": "a", "message": ""}
    )
    same = validate_event(
        {"timestamp": "2026-10-07T09:00:00+00:00", "level": "INFO", "source": "b", "message": "m"}
    )
    stats = Statistics()
    stats.add(early)
    stats.add(same)
    assert stats.to_dict()["first_timestamp"] == early.timestamp
    assert stats.to_dict()["last_timestamp"] == early.timestamp


def test_cli_writes_report_to_stdout(tmp_path: Path) -> None:
    """Проверка вывода отчёта в stdout."""
    path = tmp_path / "events.jsonl"
    event = {"timestamp": "2026-01-01T00:00:00Z", "level": "INFO", "source": "s", "message": "m"}
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")
    project_root = Path(__file__).resolve().parents[1]
    environment = {**os.environ, "PYTHONPATH": str(project_root / "src")}
    result = subprocess.run(
        [sys.executable, "-m", "streamstats", "analyze", str(path), "--format", "jsonl"],
        cwd=project_root, env=environment, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["total_events"] == 1


def test_invalid_event_field_types_are_rejected() -> None:
    """Выбрасывание исключения для некорректных типов полей."""
    record: dict[str, Any] = {
        "timestamp": "2026-01-01T00:00:00Z", "level": "INFO", "source": "s", "message": 1
    }
    with pytest.raises(InvalidEventError, match="должно быть строкой"):
        validate_event(record)
