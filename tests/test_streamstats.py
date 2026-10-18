import json
from pathlib import Path

from streamstats.analysis import Statistics, process_files
from streamstats.models import validate_event
from streamstats.parsers import parse_csv, parse_jsonl


def test_jsonl_parser(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text('{"timestamp":"2026-01-01T00:00:00Z","level":"INFO","source":"s","message":"m"}\n', encoding="utf-8")
    assert len(list(parse_jsonl(path))) == 1


def test_csv_parser(tmp_path: Path) -> None:
    path = tmp_path / "events.csv"
    path.write_text("timestamp,level,source,message\nt,INFO,s,m\n", encoding="utf-8")
    assert list(parse_csv(path))[0][1]["source"] == "s"


def test_statistics() -> None:
    event = validate_event({"timestamp": "2026-01-01T00:00:00Z", "level": "ERROR", "source": "s", "message": "m"})
    stats = Statistics()
    stats.add(event)
    assert stats.to_dict()["total_events"] == 1


def test_process_files(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    record = {"timestamp": "2026-01-01T00:00:00Z", "level": "INFO", "source": "s", "message": "m"}
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    assert process_files([str(path)], "jsonl").total == 1
