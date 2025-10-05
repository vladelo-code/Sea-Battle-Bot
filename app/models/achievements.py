from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    player_links = relationship("PlayerAchievement", back_populates="achievement")

    def __repr__(self):
        return f"<Achievement id={self.id} code={self.code}>"


class PlayerAchievement(Base):
    __tablename__ = "player_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    is_unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("player_id", "achievement_id", name="uq_player_achievement"),
    )

    player = relationship("Player")
    achievement = relationship("Achievement", back_populates="player_links")

    def __repr__(self):
        return (
            f"<PlayerAchievement id={self.id} player_id={self.player_id} "
            f"achievement_id={self.achievement_id} is_unlocked={self.is_unlocked}>"
        )


