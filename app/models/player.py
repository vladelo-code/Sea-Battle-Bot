from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)

    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=True)

    first_seen = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now)

    stats = relationship("PlayerStats", uselist=False, back_populates="player")

    def __repr__(self):
        return f"<Player id={self.id} telegram_id={self.telegram_id}>"
