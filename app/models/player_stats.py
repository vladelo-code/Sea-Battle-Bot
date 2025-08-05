from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class PlayerStats(Base):
    __tablename__ = "player_stats"

    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)

    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)

    rating = Column(Integer, default=1000)

    player = relationship("Player", back_populates="stats")

    def __repr__(self):
        return f"<Stats player_id={self.player_id} rating={self.rating}>"
