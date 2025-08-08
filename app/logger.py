import logging


def setup_logger(name: str) -> logging.Logger:
    """
    Создает и настраивает логгер с заданным именем.

    Логгер выводит сообщения в консоль с форматом:
    [ГГГГ-ММ-ДД ЧЧ:ММ:СС] сообщение

    Если у логгера уже есть обработчики, новых не добавляет.

    :param name: Имя логгера.
    :return: Настроенный экземпляр logging.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.setLevel(logging.INFO)
        logger.addHandler(console_handler)

        logger.propagate = False

    return logger
