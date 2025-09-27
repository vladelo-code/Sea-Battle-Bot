from sqlalchemy.orm import Session
from sqlalchemy import func

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


def get_top_and_bottom_players(db: Session, top_limit: int = 10, bottom_limit: int = 3, current_user_id: str = None):
    """
    Возвращает топ лучших и худших игроков по рейтингу, а также общее количество игроков.
    Если указан current_user_id и пользователь не входит в топ, возвращает его позицию.

    :param db: Сессия SQLAlchemy.
    :param top_limit: Количество лучших игроков (по умолчанию 10).
    :param bottom_limit: Количество худших игроков (по умолчанию 3).
    :param current_user_id: ID текущего пользователя для проверки его позиции.
    :return: (топ-игроки, худшие игроки, общее количество игроков, позиция текущего пользователя)
    """
    top_players = (
        db.query(Player.username, PlayerStats.rating, PlayerStats.player_id)
        .join(PlayerStats, Player.telegram_id == PlayerStats.player_id)
        .order_by(PlayerStats.rating.desc())
        .limit(top_limit)
        .all()
    )

    bottom_players = (
        db.query(Player.username, PlayerStats.rating, PlayerStats.player_id)
        .join(PlayerStats, Player.telegram_id == PlayerStats.player_id)
        .order_by(PlayerStats.rating.asc())
        .limit(bottom_limit)
        .all()
    )

    total_players = db.query(PlayerStats).count()
    
    # Получаем позицию текущего пользователя, если он указан
    current_user_position = None
    if current_user_id:
        # Проверяем, есть ли пользователь в топе
        user_in_top = any(player_id == int(current_user_id) for _, _, player_id in top_players)
        user_in_bottom = any(player_id == int(current_user_id) for _, _, player_id in bottom_players)
        
        if not user_in_top and not user_in_bottom:
            # Получаем позицию пользователя в общем рейтинге
            user_position_query = (
                db.query(Player.username, PlayerStats.rating, PlayerStats.player_id)
                .join(PlayerStats, Player.telegram_id == PlayerStats.player_id)
                .filter(PlayerStats.player_id == int(current_user_id))
                .first()
            )
            
            if user_position_query:
                # Считаем количество игроков с рейтингом выше
                higher_rated_count = (
                    db.query(func.count(PlayerStats.player_id))
                    .filter(PlayerStats.rating > user_position_query.rating)
                    .scalar()
                )
                position = higher_rated_count + 1
                current_user_position = (user_position_query.username, user_position_query.rating, position)

    return top_players, sorted(bottom_players, reverse=True), total_players, current_user_position
