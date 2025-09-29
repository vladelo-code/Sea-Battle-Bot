from sqlalchemy.orm import Session
from datetime import datetime

from app.models.bot_game_stats import BotGameStats


def get_or_create_bot_stats(db: Session, player_id: int, difficulty: str) -> BotGameStats:
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
    stats = get_or_create_bot_stats(db, player_id, difficulty)
    stats.games_played += 1
    if is_win:
        stats.wins += 1
    else:
        stats.losses += 1
    stats.last_played_at = datetime.now()
    db.commit()


def get_aggregated_bot_stats(db: Session, player_id: int) -> dict:
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
