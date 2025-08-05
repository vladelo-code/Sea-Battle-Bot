from sqlalchemy.orm import Session
from datetime import datetime

from app.models.match import Match


def create_match(db: Session, game_id: str, player_1_id: int, player_2_id: int) -> Match:
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
) -> Match | None:
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
    return db.query(Match).filter(Match.game_id == game_id).first()
