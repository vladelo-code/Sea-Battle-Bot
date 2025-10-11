from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session

from app.models import Achievement, PlayerAchievement
from app.config import MOSCOW_TZ


def seed_achievements(db: Session, definitions: list[dict]) -> None:
    """
    Создаёт записи достижений в таблице Achievement, если их ещё нет.
    """
    existing_codes = {a.code for a in db.query(Achievement).all()}
    created = False
    for item in definitions:
        if item["code"] in existing_codes:
            continue
        db.add(Achievement(
            code=item["code"],
            title=item["title"],
            description=item["description"],
            created_at=datetime.now(MOSCOW_TZ),
        ))
        created = True
    if created:
        db.commit()


def get_all_achievements(db: Session) -> List:
    """
    Возвращает список всех достижений.
    """
    return db.query(Achievement).all()


def get_achievements_by_code(db: Session) -> Dict[str, Achievement]:
    """
    Возвращает достижения в виде словаря {код: объект Achievement}.
    """
    return {a.code: a for a in get_all_achievements(db)}


def get_player_achievements(db: Session, player_id: int) -> List:
    """
    Возвращает список достижений конкретного игрока.
    """
    return db.query(PlayerAchievement).filter(PlayerAchievement.player_id == player_id).all()


def get_or_create_player_achievement(db: Session, player_id: int, achievement: Achievement) -> PlayerAchievement:
    """
    Получает или создаёт запись PlayerAchievement.
    """
    link = (
        db.query(PlayerAchievement)
        .filter(PlayerAchievement.player_id == player_id, PlayerAchievement.achievement_id == achievement.id)
        .first()
    )
    if link is None:
        link = PlayerAchievement(player_id=player_id, achievement_id=achievement.id, is_unlocked=False)
        db.add(link)
        db.commit()
        db.refresh(link)
    return link


def unlock_achievement(db: Session, link: PlayerAchievement) -> None:
    """
    Помечает достижение как разблокированное.
    """
    if link.is_unlocked:
        return
    link.is_unlocked = True
    link.unlocked_at = datetime.now(MOSCOW_TZ)
    db.commit()


def get_achievement_percentages(db: Session) -> Dict[str, float]:
    """
    Возвращает процент игроков, у которых есть каждая ачивка.
    
    Returns:
        Dict[str, float]: Словарь {код_ачивки: процент_игроков}
    """
    from app.models import Player
    
    # Получаем общее количество игроков
    total_players = db.query(Player).count()
    
    if total_players == 0:
        return {}
    
    # Получаем все ачивки
    achievements = db.query(Achievement).all()
    result = {}
    
    for achievement in achievements:
        # Считаем количество игроков с разблокированной ачивкой
        unlocked_count = (
            db.query(PlayerAchievement)
            .filter(
                PlayerAchievement.achievement_id == achievement.id,
                PlayerAchievement.is_unlocked == True
            )
            .count()
        )
        
        # Вычисляем процент
        percentage = (unlocked_count / total_players) * 100
        result[achievement.code] = round(percentage, 1)
    
    return result
