from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class BotGameStats(Base):
    __tablename__ = "bot_game_stats"

    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    difficulty = Column(String, primary_key=True)  # "easy" | "medium" | "hard"

    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)

    last_played_at = Column(DateTime, default=datetime.now)

    player = relationship("Player")

    def __repr__(self):
        return (
            f"<BotGameStats player_id={self.player_id} diff={self.difficulty} "
            f"games={self.games_played} wins={self.wins} losses={self.losses}>"
        )
