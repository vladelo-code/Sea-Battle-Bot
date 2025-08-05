from sqlalchemy.orm import Session
from datetime import datetime
from app.models.player import Player


def get_or_create_player(db: Session, telegram_id: str, username: str | None = None) -> Player:
    player = db.query(Player).filter(Player.telegram_id == telegram_id).first()

    if player:
        # Обновляем дату последнего появления и, при необходимости, username
        player.last_seen = datetime.now()
        if username and player.username != username:
            player.username = username
    else:
        player = Player(
            telegram_id=telegram_id,
            username=username,
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )
        db.add(player)
        db.commit()
        db.refresh(player)

    db.commit()
    db.refresh(player)
    return player


def get_player_by_telegram_id(db: Session, telegram_id: str) -> Player | None:
    return db.query(Player).filter(Player.telegram_id == telegram_id).first()
