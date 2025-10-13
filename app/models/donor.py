from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class Donor(Base):
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.telegram_id"), nullable=False, unique=True)
    is_donor = Column(Boolean, default=False)
    donation_date = Column(DateTime, nullable=True)
    stars_amount = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    player = relationship("Player", backref="donor_info")

    def __repr__(self):
        return f"<Donor id={self.id} player_id={self.player_id} is_donor={self.is_donor}>"
