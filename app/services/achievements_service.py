from datetime import datetime, timedelta
from typing import Type
from sqlalchemy.orm import Session

from app.models import Achievement, PlayerAchievement, Match, BotGameStats
from app.config import ACHIEVEMENT_DEFINITIONS, ADMIN_ID
from app.config import MOSCOW_TZ
from app.db_utils.achievements import (
    seed_achievements,
    get_achievements_by_code,
    get_or_create_player_achievement,
    unlock_achievement,
)


def _unlock_by_code(db: Session, player_id: int, achievements_by_code: dict[str, Achievement], code: str) -> None:
    """
    Разблокирует достижение по его коду для конкретного игрока.

    Функция получает объект достижения по коду, создаёт запись PlayerAchievement,
    если её ещё нет, и помечает достижение как разблокированное.

    Args:
        db (Session): Активная сессия SQLAlchemy для работы с базой данных.
        player_id (int): ID игрока, которому нужно выдать достижение.
        achievements_by_code (dict[str, Achievement]): Словарь достижений, где ключ — код, значение — объект Achievement.
        code (str): Уникальный код достижения (например, "fleet_marathon" или "speedrunner").

    Returns:
        None
    """
    achievement = achievements_by_code.get(code)
    if not achievement:
        return
    link = get_or_create_player_achievement(db, player_id, achievement)
    unlock_achievement(db, link)


def evaluate_achievements_after_bot_game(db: Session, player_id: int) -> None:
    """
    Проверяет и назначает достижения после игр с ботами.
    """
    seed_achievements(db, ACHIEVEMENT_DEFINITIONS)
    achievements_by_code = get_achievements_by_code(db)

    stats = {s.difficulty: s for s in db.query(BotGameStats).filter_by(player_id=player_id).all()}
    easy, medium, hard = stats.get("easy"), stats.get("medium"), stats.get("hard")

    # 1) full_captain_course — сыграй хотя бы 1 матч на каждом уровне с ботом
    if easy and medium and hard and all(s.games_played > 0 for s in [easy, medium, hard]):
        _unlock_by_code(db, player_id, achievements_by_code, "full_captain_course")

    # 2) fleet_marathon — суммарно 50 матчей с ботом
    total_games = sum(s.games_played for s in stats.values())
    if total_games >= 50:
        _unlock_by_code(db, player_id, achievements_by_code, "fleet_marathon")

    # 7) easy_breeze — 20 побед на easy
    if easy and easy.wins >= 20:
        _unlock_by_code(db, player_id, achievements_by_code, "easy_breeze")

    # 8) medium_master — 10 побед на medium
    if medium and medium.wins >= 10:
        _unlock_by_code(db, player_id, achievements_by_code, "medium_master")

    # 9) hard_master — 5 побед на hard
    if hard and hard.wins >= 5:
        _unlock_by_code(db, player_id, achievements_by_code, "hard_master")


def evaluate_achievements_after_multiplayer_match(db: Session, match: Type[Match]) -> None:
    """
    Проверяет и назначает достижения после мультиплеерных матчей.
    """
    seed_achievements(db, ACHIEVEMENT_DEFINITIONS)
    achievements_by_code = get_achievements_by_code(db)

    if not match.ended_at or not match.started_at:
        db.refresh(match)

    duration = (match.ended_at - match.started_at) if match.ended_at and match.started_at else None

    # 3) speedrunner — победа <= 60 секунд
    if match.winner_id and duration and duration <= timedelta(seconds=60) and match.result == "normal":
        _unlock_by_code(db, match.winner_id, achievements_by_code, "speedrunner")

    # 4) night_hunter — матч между 00:00 и 03:00 МСК
    # 5) morning_sailor — матч между 05:00 и 08:00 МСК
    if match.started_at:
        hour = match.started_at.hour
        for pid in [match.player_1_id, match.player_2_id]:
            if 0 <= hour < 3:
                _unlock_by_code(db, pid, achievements_by_code, "night_hunter")
            if 5 <= hour < 8:
                _unlock_by_code(db, pid, achievements_by_code, "morning_sailor")

    # 6) win_streak_10 — 10 побед подряд в мультиплеере
    # 10) brave_loser — 5 поражений подряд (без сдачи)
    def _get_recent_results(pid: int, limit: int = 20) -> list[tuple[bool, str]]:
        rows = (
            db.query(Match)
            .filter(((Match.player_1_id == pid) | (Match.player_2_id == pid)) & (Match.ended_at.isnot(None)))
            .order_by(Match.ended_at.desc())
            .limit(limit)
            .all()
        )
        out: list[tuple[bool, str]] = []
        for m in rows:
            is_win = m.winner_id == pid
            out.append((is_win, m.result or ""))
        return list(reversed(out))

    for pid in [match.player_1_id, match.player_2_id]:
        recent = _get_recent_results(pid, limit=30)

        # победная серия
        best_win_streak = 0
        cur = 0
        for is_win, _ in recent:
            if is_win:
                cur += 1
                best_win_streak = max(best_win_streak, cur)
            else:
                cur = 0
        if best_win_streak >= 10:
            _unlock_by_code(db, pid, achievements_by_code, "win_streak_10")

        # серия поражений без сдачи
        best_lose_streak = 0
        cur = 0
        for is_win, result in recent:
            if (not is_win) and (result != "surrender"):
                cur += 1
                best_lose_streak = max(best_lose_streak, cur)
            else:
                cur = 0
        if best_lose_streak >= 5:
            _unlock_by_code(db, pid, achievements_by_code, "brave_loser")

    # 11) week_streak — каждый день хотя бы 1 матч в течение 7 дней
    def _has_7_day_streak(pid: int) -> bool:
        rows = (
            db.query(Match)
            .filter(((Match.player_1_id == pid) | (Match.player_2_id == pid)) & (Match.ended_at.isnot(None)))
            .order_by(Match.ended_at.desc())
            .limit(100)
            .all()
        )
        days: set[str] = set()
        for m in rows:
            d = (m.ended_at or m.started_at).date()
            days.add(str(d))
        today = datetime.now(MOSCOW_TZ).date()
        for start_offset in range(0, 21):
            ok = True
            for i in range(7):
                day = today - timedelta(days=start_offset + i)
                if str(day) not in days:
                    ok = False
                    break
            if ok:
                return True
        return False

    for pid in [match.player_1_id, match.player_2_id]:
        if _has_7_day_streak(pid):
            _unlock_by_code(db, pid, achievements_by_code, "week_streak")

    # 12) fan_dev — сыграй матч с разработчиком (@vladelo)
    if int(ADMIN_ID) in [match.player_1_id, match.player_2_id]:
        for pid in [match.player_1_id, match.player_2_id]:
            _unlock_by_code(db, pid, achievements_by_code, "fan_dev")


def get_player_achievements(db: Session, player_id: int) -> list[dict]:
    """
    Возвращает все достижения с флагом разблокировки.
    """
    seed_achievements(db, ACHIEVEMENT_DEFINITIONS)
    achievements = db.query(Achievement).all()
    links = db.query(PlayerAchievement).filter(PlayerAchievement.player_id == player_id).all()
    by_id = {l.achievement_id: l for l in links}
    result: list[dict] = []
    for a in achievements:
        link = by_id.get(a.id)
        result.append({
            "code": a.code,
            "title": a.title,
            "description": a.description,
            "is_unlocked": bool(link.is_unlocked) if link else False,
            "unlocked_at": link.unlocked_at if link else None,
        })
    return result
