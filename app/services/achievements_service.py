from datetime import datetime, timedelta
from typing import Type
from sqlalchemy.orm import Session

from app.models import Achievement, PlayerAchievement, Match, BotGameStats
from app.config import ACHIEVEMENT_DEFINITIONS, ADMIN_ID


def seed_achievements(db: Session) -> None:
    existing_codes = {a.code for a in db.query(Achievement).all()}
    created = False
    for item in ACHIEVEMENT_DEFINITIONS:
        if item["code"] in existing_codes:
            continue
        db.add(Achievement(
            code=item["code"],
            title=item["title"],
            description=item["description"],
            created_at=datetime.now(),
        ))
        created = True
    if created:
        db.commit()


def _get_or_create_player_achievement(db: Session, player_id: int, achievement: Achievement) -> PlayerAchievement:
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


def _unlock(db: Session, link: PlayerAchievement) -> None:
    if link.is_unlocked:
        return
    link.is_unlocked = True
    link.unlocked_at = datetime.now()
    db.commit()


def evaluate_achievements_after_bot_game(db: Session, player_id: int) -> None:
    seed_achievements(db)

    achievements_by_code = {a.code: a for a in db.query(Achievement).all()}

    # 1) full_captain_course — сыграй хотя бы 1 матч на каждом уровне с ботом
    easy = db.query(BotGameStats).filter_by(player_id=player_id, difficulty="easy").first()
    medium = db.query(BotGameStats).filter_by(player_id=player_id, difficulty="medium").first()
    hard = db.query(BotGameStats).filter_by(player_id=player_id, difficulty="hard").first()
    if easy and easy.games_played > 0 and medium and medium.games_played > 0 and hard and hard.games_played > 0:
        link = _get_or_create_player_achievement(db, player_id, achievements_by_code["full_captain_course"])
        _unlock(db, link)

    # 2) fleet_marathon — суммарно 50 матчей с ботом
    total_games = 0
    for s in db.query(BotGameStats).filter(BotGameStats.player_id == player_id).all():
        total_games += s.games_played
    if total_games >= 50:
        link = _get_or_create_player_achievement(db, player_id, achievements_by_code["fleet_marathon"])
        _unlock(db, link)

    # 7) easy_breeze — 20 побед на easy
    if easy and easy.wins >= 20:
        link = _get_or_create_player_achievement(db, player_id, achievements_by_code["easy_breeze"])
        _unlock(db, link)

    # 8) medium_master — 10 побед на medium
    if medium and medium.wins >= 10:
        link = _get_or_create_player_achievement(db, player_id, achievements_by_code["medium_master"])
        _unlock(db, link)

    # 9) hard_master — 5 побед на hard
    if hard and hard.wins >= 5:
        link = _get_or_create_player_achievement(db, player_id, achievements_by_code["hard_master"])
        _unlock(db, link)


def evaluate_achievements_after_multiplayer_match(db: Session, match: Type[Match]) -> None:
    seed_achievements(db)

    achievements_by_code = {a.code: a for a in db.query(Achievement).all()}

    if not match.ended_at or not match.started_at:
        db.refresh(match)

    duration = (match.ended_at - match.started_at) if match.ended_at and match.started_at else None

    # 3) speedrunner — победа <= 60 секунд
    if match.winner_id and duration and duration <= timedelta(seconds=60) and match.result == "normal":
        link = _get_or_create_player_achievement(db, match.winner_id, achievements_by_code["speedrunner"])
        _unlock(db, link)

    # 4) night_hunter — матч между 00:00 и 03:00 МСК
    # 5) morning_sailor — матч между 05:00 и 08:00 МСК
    # Предполагаем, что timestamps в МСК или приводятся к нему заранее.
    if match.started_at:
        hour = match.started_at.hour
        for pid in [match.player_1_id, match.player_2_id]:
            if 0 <= hour < 3:
                link = _get_or_create_player_achievement(db, pid, achievements_by_code["night_hunter"])
                _unlock(db, link)
            if 5 <= hour < 8:
                link = _get_or_create_player_achievement(db, pid, achievements_by_code["morning_sailor"])
                _unlock(db, link)

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
            link = _get_or_create_player_achievement(db, pid, achievements_by_code["win_streak_10"])
            _unlock(db, link)

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
            link = _get_or_create_player_achievement(db, pid, achievements_by_code["brave_loser"])
            _unlock(db, link)

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
        # проверяем наличие хотя бы одного матча в каждый из 7 подряд идущих дней, заканчивающихся сегодня
        today = datetime.now().date()
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
            link = _get_or_create_player_achievement(db, pid, achievements_by_code["week_streak"])
            _unlock(db, link)

    # 12) fan_dev — сыграй матч с разработчиком (@vladelo)
    if int(ADMIN_ID) in [match.player_1_id, match.player_2_id]:
        for pid in [match.player_1_id, match.player_2_id]:
            link = _get_or_create_player_achievement(db, pid, achievements_by_code["fan_dev"])
            _unlock(db, link)


def get_player_achievements(db: Session, player_id: int) -> list[dict]:
    seed_achievements(db)
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
