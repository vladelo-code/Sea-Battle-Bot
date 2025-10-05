from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.player import Player
from app.models.player_stats import PlayerStats
from app.models.match import Match
from app.db_utils.stats import get_stats, get_or_create_stats
from app.config import MOSCOW_TZ


def get_or_create_player(db: Session, telegram_id: str, username: str | None = None) -> Player:
    """
    Получает игрока по Telegram ID или создает нового, если он не существует.

    Если игрок найден:
      - обновляется время последнего появления (last_seen)
      - обновляется username, если он изменился

    Если игрок не найден:
      - создается новый игрок с текущим временем регистрации и последнего появления
      - для созданного игрока создается пустая строка статистики (чтобы он учитывался в общем рейтинге)

    :param db: Сессия SQLAlchemy.
    :param telegram_id: Telegram ID пользователя.
    :param username: Username пользователя (может быть None).
    :return: Объект Player.
    """
    player = db.query(Player).filter(Player.telegram_id == telegram_id).first()

    if player:
        # Обновляем дату последнего появления и, при необходимости, username
        player.last_seen = datetime.now(MOSCOW_TZ)
        if player.username != username:
            player.username = username
    else:
        player = Player(
            telegram_id=telegram_id,
            username=username,
            first_seen=datetime.now(MOSCOW_TZ),
            last_seen=datetime.now(MOSCOW_TZ)
        )
        db.add(player)
        db.commit()
        db.refresh(player)

        # Создаём статистику игроку сразу при регистрации
        get_or_create_stats(db, player_id=int(player.telegram_id))

    db.commit()
    db.refresh(player)
    return player


def get_player_by_telegram_id(db: Session, telegram_id: str) -> Player | None:
    """
    Получает игрока по его Telegram ID.

    :param db: Сессия SQLAlchemy.
    :param telegram_id: Telegram ID пользователя.
    :return: Объект Player, если найден, иначе None.
    """
    return db.query(Player).filter(Player.telegram_id == telegram_id).first()


def get_extended_stats(db: Session, telegram_id: str) -> dict | None:
    """
    Возвращает расширенную статистику игрока:
    - количество игр, побед, поражений
    - рейтинг и место в рейтинге
    - дата регистрации и последнего визита
    - среднее и суммарное время матчей
    """
    player = get_player_by_telegram_id(db, telegram_id)
    stats = get_stats(db, int(telegram_id))
    if not player or not stats:
        return None

    higher_count = (
        db.query(func.count(PlayerStats.player_id))
        .filter(PlayerStats.rating > stats.rating)
        .scalar()
    )
    place = higher_count + 1
    total_players = db.query(func.count(PlayerStats.player_id)).scalar()

    matches = (
        db.query(Match)
        .filter((Match.player_1_id == player.telegram_id) | (Match.player_2_id == player.telegram_id))
        .filter(Match.ended_at.isnot(None))
        .all()
    )

    durations = [
        (m.ended_at - m.started_at).total_seconds()
        for m in matches
        if m.started_at and m.ended_at
    ]

    total_time = sum(durations) if durations else 0
    avg_time = total_time / len(durations) if durations else 0

    return {
        "games_played": stats.games_played,
        "wins": stats.wins,
        "losses": stats.losses,
        "rating": stats.rating,
        "place": place,
        "total_players": total_players,
        "first_seen": player.first_seen,
        "last_seen": player.last_seen,
        "avg_time": avg_time,
        "total_time": total_time,
    }
