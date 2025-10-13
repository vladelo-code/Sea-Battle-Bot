from sqlalchemy.orm import Session
from datetime import datetime

from app.models.bot_game_stats import BotGameStats
from app.config import MOSCOW_TZ


def get_or_create_bot_stats(db: Session, player_id: int, difficulty: str) -> BotGameStats:
    """
    Получает объект статистики игр против бота для конкретного игрока и уровня сложности.
    Если статистика ещё не создана, создаёт новую запись.

    Args:
        db (Session): SQLAlchemy сессия базы данных.
        player_id (int): ID игрока.
        difficulty (str): Уровень сложности ("easy", "medium", "hard", "super_hard").

    Returns:
        BotGameStats: объект статистики для указанного игрока и уровня сложности.
    """
    stats = (
        db.query(BotGameStats)
        .filter(BotGameStats.player_id == player_id, BotGameStats.difficulty == difficulty)
        .first()
    )
    if stats is None:
        stats = BotGameStats(player_id=player_id, difficulty=difficulty)
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


def increment_bot_game_result(db: Session, player_id: int, difficulty: str, is_win: bool) -> None:
    """
    Обновляет статистику игр против бота для указанного игрока:
    увеличивает количество сыгранных игр, побед или поражений, а также время последней игры.

    Args:
        db (Session): SQLAlchemy сессия базы данных.
        player_id (int): ID игрока.
        difficulty (str): Уровень сложности ("easy", "medium", "hard").
        is_win (bool): True, если игрок выиграл, False если проиграл.

    Returns:
        None
    """
    stats = get_or_create_bot_stats(db, player_id, difficulty)
    stats.games_played += 1
    if is_win:
        stats.wins += 1
    else:
        stats.losses += 1
    stats.last_played_at = datetime.now(MOSCOW_TZ)
    db.commit()


def get_aggregated_bot_stats(db: Session, player_id: int) -> dict:
    """
    Получает агрегированную статистику игр против бота для указанного игрока.
    Включает суммарное количество игр, побед, поражений, а также разбивку по уровням сложности.

    Args:
        db (Session): SQLAlchemy сессия базы данных.
        player_id (int): ID игрока.

    Returns:
        dict: словарь со следующей структурой:
            {
                "total_games": int,
                "total_wins": int,
                "total_losses": int,
                "by_difficulty": {
                    "easy": {"games": int, "wins": int, "losses": int, "last_played_at": datetime},
                    "medium": {...},
                    "hard": {...},
                    "super_hard": {...}
                }
            }
    """
    rows = (
        db.query(BotGameStats)
        .filter(BotGameStats.player_id == player_id)
        .all()
    )
    agg = {
        "total_games": 0,
        "total_wins": 0,
        "total_losses": 0,
        "by_difficulty": {},
    }
    for r in rows:
        agg["total_games"] += r.games_played
        agg["total_wins"] += r.wins
        agg["total_losses"] += r.losses
        agg["by_difficulty"][r.difficulty] = {
            "games": r.games_played,
            "wins": r.wins,
            "losses": r.losses,
            "last_played_at": r.last_played_at,
        }
    return agg
