import json
from pathlib import Path
from typing import Any


def write_report(report: dict[str, Any], output: str | None) -> None:
    """Запись JSON отчёта в UTF-8."""
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if output is None:
        print(text, end="")
    else:
        Path(output).write_text(text, encoding="utf-8")
