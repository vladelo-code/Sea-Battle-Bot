from typing import Type
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.match import Match


def create_match(db: Session, game_id: str, player_1_id: int, player_2_id: int) -> Match:
    """
    Создает новую запись о матче в базе данных.

    :param db: Сессия SQLAlchemy.
    :param game_id: Уникальный идентификатор игры.
    :param player_1_id: ID первого игрока.
    :param player_2_id: ID второго игрока.
    :return: Объект Match, представляющий созданный матч.
    """
    match = Match(
        game_id=game_id,
        player_1_id=player_1_id,
        player_2_id=player_2_id,
        started_at=datetime.now(),
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def update_match_result(
        db: Session,
        game_id: str,
        winner_id: int = None,
        result: str = None,
        ended_at: datetime = None,
) -> Type[Match] | None:
    """
    Обновляет информацию о завершившемся матче.

    :param db: Сессия SQLAlchemy.
    :param game_id: Уникальный идентификатор игры.
    :param winner_id: ID победителя (если есть).
    :param result: Тип завершения матча (например, 'surrender', 'win').
    :param ended_at: Время окончания матча (по умолчанию текущее время).
    :return: Обновленный объект Match или None, если матч не найден.
    """
    match = db.query(Match).filter(Match.game_id == game_id).first()
    if not match:
        return None
    if winner_id:
        match.winner_id = winner_id
    if result:
        match.result = result
    match.ended_at = ended_at or datetime.now()
    db.commit()
    db.refresh(match)
    return match


def get_match_by_game_id(db: Session, game_id: str) -> Match | None:
    """
    Возвращает матч по ID игры.

    :param db: Сессия SQLAlchemy.
    :param game_id: Уникальный идентификатор игры.
    :return: Объект Match, если найден, иначе None.
    """
    return db.query(Match).filter(Match.game_id == game_id).first()
