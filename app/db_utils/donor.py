from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Donor
from app.db_utils.achievements import get_achievements_by_code, get_or_create_player_achievement, unlock_achievement


def is_donor(db: Session, player_id: int) -> bool:
    """
    Проверяет, является ли игрок донором.
    """
    donor = db.query(Donor).filter(Donor.player_id == player_id).first()
    return donor is not None and donor.is_donor


def get_donor(db: Session, player_id: int) -> Donor | None:
    """
    Возвращает запись донора по player_id.
    """
    return db.query(Donor).filter(Donor.player_id == player_id).first()


def mark_as_donor(db: Session, player, stars_amount: int, payment_date: datetime) -> Donor:
    """
    Помечает игрока как донора или обновляет запись.
    """
    donor = get_donor(db, player.telegram_id)

    if donor:
        donor.is_donor = True
        donor.donation_date = payment_date
        donor.stars_amount = stars_amount
    else:
        donor = Donor(
            player_id=player.telegram_id,
            is_donor=True,
            donation_date=payment_date,
            stars_amount=stars_amount
        )
        db.add(donor)

    return donor


def handle_donation(db, player, stars_amount: int, payment_date):
    """
    Выполняет полную обработку доната:
    - Помечает игрока как донора;
    - Выдаёт ачивку "Поддержал проект";
    - Сохраняет изменения.
    """
    mark_as_donor(db, player, stars_amount, payment_date)

    achievements_by_code = get_achievements_by_code(db)
    if "project_supporter" in achievements_by_code:
        achievement = achievements_by_code["project_supporter"]
        player_achievement = get_or_create_player_achievement(db, player.telegram_id, achievement)
        unlock_achievement(db, player_achievement)

    db.commit()
