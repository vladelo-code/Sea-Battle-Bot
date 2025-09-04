from sqlalchemy.orm import Session

from app.models.player_stats import PlayerStats
from app.models.player import Player
from app.utils.rating import calculate_elo


def get_or_create_stats(db: Session, player_id: int) -> PlayerStats:
    """
    Получает статистику игрока по ID или создает новую запись, если она отсутствует.

    :param db: Сессия SQLAlchemy.
    :param player_id: ID игрока.
    :return: Объект PlayerStats.
    """
    stats = db.query(PlayerStats).filter_by(player_id=player_id).first()
    if not stats:
        stats = PlayerStats(player_id=player_id)
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


def update_stats_after_match(db: Session, winner_id: int, loser_id: int) -> None:
    """
    Обновляет статистику игроков после завершения матча.

    У победителя:
      - увеличивается счетчик игр и побед.
    У проигравшего:
      - увеличивается счетчик игр и поражений.
    Также пересчитывается рейтинг Elo.

    :param db: Сессия SQLAlchemy.
    :param winner_id: ID победителя.
    :param loser_id: ID проигравшего.
    """
    winner_stats = get_or_create_stats(db, winner_id)
    loser_stats = get_or_create_stats(db, loser_id)

    winner_stats.games_played += 1
    winner_stats.wins += 1

    loser_stats.games_played += 1
    loser_stats.losses += 1

    winner_stats.rating, loser_stats.rating = calculate_elo(
        winner_rating=winner_stats.rating,
        loser_rating=loser_stats.rating,
    )

    db.commit()


def get_stats(db: Session, player_id: int) -> PlayerStats | None:
    """
    Получает статистику игрока по его ID.

    :param db: Сессия SQLAlchemy.
    :param player_id: ID игрока.
    :return: Объект PlayerStats, если найден, иначе None.
    """
    return db.query(PlayerStats).filter_by(player_id=player_id).first()


def get_top_players(db: Session, limit: int = 10):
    """
    Возвращает список топ игроков по рейтингу и общее количество игроков.

    :param db: Сессия SQLAlchemy.
    :param limit: Количество лучших игроков в выдаче (по умолчанию 10).
    :return: (список игроков, общее количество игроков)
    """
    results = (
        db.query(Player.username, PlayerStats.rating)
        .join(PlayerStats, Player.telegram_id == PlayerStats.player_id)
        .order_by(PlayerStats.rating.desc())
        .limit(limit)
        .all()
    )

    total_players = db.query(PlayerStats).count()

    return results, total_players
