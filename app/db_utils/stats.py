from sqlalchemy.orm import Session

from app.models.player_stats import PlayerStats
from app.models.player import Player

from app.utils.rating import calculate_elo


def get_or_create_stats(db: Session, player_id: int) -> PlayerStats:
    stats = db.query(PlayerStats).filter_by(player_id=player_id).first()
    if not stats:
        stats = PlayerStats(player_id=player_id)
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


def update_stats_after_match(db: Session, winner_id: int, loser_id: int) -> None:
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
    return db.query(PlayerStats).filter_by(player_id=player_id).first()


def get_top_players(db: Session, limit: int = 10) -> list[tuple[str, int]]:
    results = (
        db.query(Player.username, PlayerStats.rating)
        .join(PlayerStats, Player.telegram_id == PlayerStats.player_id)
        .order_by(PlayerStats.rating.desc())
        .limit(limit)
        .all()
    )
    return results
