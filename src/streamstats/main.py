import argparse
import logging
import sys

from streamstats.analysis import process_files
from streamstats.errors import StreamStatsError
from streamstats.report import write_report


def main(argv: list[str] | None = None) -> int:
    """Запускает команду и возвращает код выхода."""
    parser = argparse.ArgumentParser(
        prog="streamstats", description="Чтение логов и вывод статистики."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    analyze = commands.add_parser("analyze", help="Анализ CSV или JSONL логов")
    analyze.add_argument("input", nargs="+", help="Входные файлы")
    analyze.add_argument(
        "--format", required=True, choices=("csv", "jsonl"), help="Формат входных файлов"
    )
    analyze.add_argument("--output", help="Файл для записи статистики (stdout, если не указано)")
    analyze.add_argument("--skip-invalid", action="store_true", help="Пропуск некорректных строк")
    args = parser.parse_args(argv)

    logger = logging.getLogger("streamstats")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for old_handler in logger.handlers[:]:
        logger.removeHandler(old_handler)
        old_handler.close()

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
    logger.addHandler(handler)

    try:
        logger.info("Обработка входных файлов (%d)", len(args.input))
        stats = process_files(args.input, args.format, args.skip_invalid)
        write_report(stats.to_dict(), args.output)
        logging.getLogger("streamstats").info("Корректных записей обработано: %d", stats.total)
        return 0
    except StreamStatsError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"Не удалось записать отчёт: {error}", file=sys.stderr)
        return 2
