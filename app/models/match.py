from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)

    player_1_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    player_2_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.now)
    ended_at = Column(DateTime, nullable=True)

    # Результат игры: surrender, timeout
    result = Column(String, nullable=True)

    player_1 = relationship("Player", foreign_keys=[player_1_id])
    player_2 = relationship("Player", foreign_keys=[player_2_id])
    winner = relationship("Player", foreign_keys=[winner_id])

    def __repr__(self):
        return f"<Match id={self.id} p1={self.player_1_id} p2={self.player_2_id} winner={self.winner_id}>"
