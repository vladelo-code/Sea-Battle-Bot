import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Добавление пути к приложению
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импорт Base из проекта
from app.models import Base

# Импорт всех моделей, чтобы Alembic увидел их
import app.models

# Alembic Config object
config = context.config

# Настройка логирования из файла конфигурации
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для автоматического создания таблиц
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Запуск миграций в оффлайн-режиме.
    Без подключения к базе, просто генерирует SQL.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Запуск миграций в онлайн-режиме.
    Подключается к базе и применяет миграции.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# Определение режима запуска
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
