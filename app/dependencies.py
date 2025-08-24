from typing import Generator
from contextlib import contextmanager
from sqlalchemy.orm import Session

from app.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Генератор для получения сессии БД.
    Используется как зависимость или вручную с next().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Контекстный менеджер для работы с БД.
    Используется как:
        with db_session() as db:
            ...
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        yield db
    finally:
        db_gen.close()
