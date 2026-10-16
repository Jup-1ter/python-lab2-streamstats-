class StreamStatsError(Exception):
    """Базовое исключение."""


class UnsupportedFormatError(StreamStatsError):
    """Исключение для неподдерживаемого формата"""


class InvalidEventError(StreamStatsError):
    """Исключение нарушения модели события"""


class InvalidTimestampError(InvalidEventError):
    """Исключение некорректной временной метки"""


class CLIConfigurationError(StreamStatsError):
    """Исключение некорректных параметров командной строки или доступа"""
