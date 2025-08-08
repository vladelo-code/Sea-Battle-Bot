from sqlalchemy.orm import Session
from app.db_utils.player import get_or_create_player


def register_or_update_player(db: Session, telegram_id: str, username: str):
    """
    Регистрирует нового игрока или обновляет данные существующего в базе данных.

    :param db: Сессия базы данных.
    :param telegram_id: Telegram ID пользователя.
    :param username: Username пользователя.
    :return: Объект Player, созданный или обновленный в базе.
    """
    return get_or_create_player(db, telegram_id, username)
