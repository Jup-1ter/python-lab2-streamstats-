# streamstats

streamstats: чтение CSV и JSONL логов, валидация событий, потоковый сбор статистики и составление JSON отчёта.

## Файлы

- `src/streamstats/constants.py`: константы
- `src/streamstats/errors.py`: собственные ошибки
- `src/streamstats/models.py`: валидация событий и парсинг временных меток
- `src/streamstats/parsers.py`: потоковое чтение CSV и JSONL
- `src/streamstats/analysis.py`: составление статистики
- `src/streamstats/report.py`: вывод JSON отчёта
- `src/streamstats/main.py`, `__main__.py`: CLI и точка входа
- `tests/`: тесты
- `pyproject.toml`, `uv.lock`: настройки проекта и зависимостей

## Установка

Требуется Python 3.12 или новее и `uv`.

```sh
uv sync
source .venv/bin/activate
pre-commit install
```

## Использование

```sh
python -m streamstats --help
python -m streamstats analyze events.csv --format csv --output report.json
python -m streamstats analyze first.jsonl second.jsonl --format jsonl
python -m streamstats analyze events.jsonl --format jsonl --skip-invalid
```

Без `--output` отчёт будет выведен в stdout.
По уомлчанию некорректные входные данные останавливают обработку с кодом 2.
При указании `--skip-invalid` о некорректных записях сообщается в логах и отчёте.

## JSON отчёт

- `total_events`: количество корректных событий.
- `events_per_level`: количество `DEBUG`, `INFO`, `WARNING`, `ERROR` и `CRITICAL` по отдельности.
- `events_per_source`: количество событий от каждого источника.
- `top_error_sources`: топ-5 источников с наибольшим количеством `ERROR` и `CRITICAL`. Состоит из объектов с полями `source` и `count`.
- `first_timestamp`: самая ранняя временная ветка, которая была встречена в логах. null, если корректных событий не было.
- `last_timestamp`: самая поздняя временная ветка, которая была встречена в логах. null, если корректных событий не было.
- `skipped_invalid_lines`: количество пропущенных некорректных строк.

Каждое событие должно содержать поля `timestamp`, `level`, `source` и `message`. Временные ветки в формате ISO 8601, временные метки без смещения считаются как UTC. Пустое `message` разрешено, пустой `source` — нет.

## Проверки

```sh
python -m pytest
ruff check .
mypy
```
