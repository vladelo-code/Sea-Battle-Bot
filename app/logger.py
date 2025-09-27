import logging
from pathlib import Path


def setup_logger(name: str, log_file: str = "bot.log") -> logging.Logger:
    """
    Создает и настраивает логгер с заданным именем.
    Логгер выводит сообщения в консоль и записывает их в файл с форматом:
    [ГГГГ-ММ-ДД ЧЧ:ММ:СС] сообщение

    :param name: Имя логгера.
    :param log_file: Путь к файлу для логов (по умолчанию "bot.log").
    :return: Настроенный экземпляр logging.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

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
