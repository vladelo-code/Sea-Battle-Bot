import logging
from pathlib import Path
from datetime import datetime

from app.config import MOSCOW_TZ


def moscow_time(*args):
    return datetime.now(MOSCOW_TZ).timetuple()


def setup_logger(name: str, log_file: str = "bot.log") -> logging.Logger:
    """
    Создает и настраивает логгер с часовым поясом МСК.
    Логгер выводит сообщения в консоль и записывает их в файл с форматом:
    [ГГГГ-ММ-ДД ЧЧ:ММ:СС] сообщение
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        formatter.converter = moscow_time

        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Файловый обработчик
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)

        logger.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        logger.propagate = False

    return logger
