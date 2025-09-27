from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, cast, String
from datetime import datetime, timedelta

from app.models.match import Match
from app.models.player import Player


def get_fastest_game(db: Session) -> Optional[Tuple[Match, str, str]]:
    """
    Получает самую быструю игру (минимальное время между started_at и ended_at).
    Учитывает только игры со статусом 'normal'.
    
    :param db: Сессия SQLAlchemy
    :return: Кортеж (Match, username_1, username_2) или None
    """
    # Получаем все игры со статусом 'normal' и с завершенным временем
    matches = db.query(Match).filter(
        and_(
            Match.result == 'normal',
            Match.ended_at.isnot(None)
        )
    ).all()
    
    if not matches:
        return None
    
    fastest_match = None
    min_duration = None
    
    # Находим самую быструю игру
    for match in matches:
        try:
            # Проверяем, что это объекты datetime
            if isinstance(match.started_at, str):
                started_at = datetime.fromisoformat(match.started_at.replace('Z', '+00:00'))
            else:
                started_at = match.started_at
                
            if isinstance(match.ended_at, str):
                ended_at = datetime.fromisoformat(match.ended_at.replace('Z', '+00:00'))
            else:
                ended_at = match.ended_at
            
            duration = ended_at - started_at
            
            if min_duration is None or duration < min_duration:
                min_duration = duration
                fastest_match = match
                
        except (ValueError, TypeError) as e:
            # Пропускаем игры с некорректными датами
            continue
    
    if not fastest_match:
        return None
    
    # Получаем username'ы игроков по telegram_id
    player1 = db.query(Player).filter(Player.telegram_id == str(fastest_match.player_1_id)).first()
    player2 = db.query(Player).filter(Player.telegram_id == str(fastest_match.player_2_id)).first()
    
    player1_username = player1.username if player1 and player1.username else "Неизвестный игрок"
    player2_username = player2.username if player2 and player2.username else "Неизвестный игрок"
    
    return fastest_match, player1_username, player2_username


def get_longest_win_streak(db: Session) -> Optional[Tuple[int, str]]:
    """
    Получает самый долгий стрик побед (количество побед подряд).
    
    :param db: Сессия SQLAlchemy
    :return: Кортеж (количество побед, username) или None
    """
    # Получаем все игры со статусом 'normal', отсортированные по времени
    games = db.query(Match).filter(
        and_(
            Match.result == 'normal',
            Match.ended_at.isnot(None),
            Match.winner_id.isnot(None)
        )
    ).order_by(Match.ended_at.asc()).all()
    
    if not games:
        return None
    
    # Группируем игры по игрокам
    player_games = {}
    for game in games:
        winner_id = game.winner_id
        if winner_id not in player_games:
            player_games[winner_id] = []
        player_games[winner_id].append(game)
    
    max_streak = 0
    best_player_id = None
    
    # Для каждого игрока ищем самый длинный стрик побед
    for player_id, player_games_list in player_games.items():
        current_streak = 0
        max_current_streak = 0
        
        for game in player_games_list:
            if game.winner_id == player_id:
                current_streak += 1
                max_current_streak = max(max_current_streak, current_streak)
            else:
                current_streak = 0
        
        if max_current_streak > max_streak:
            max_streak = max_current_streak
            best_player_id = player_id
    
    if best_player_id is None:
        return None
    
    # Получаем username игрока по telegram_id
    player = db.query(Player).filter(Player.telegram_id == str(best_player_id)).first()
    username = player.username if player and player.username else "Неизвестный игрок"
    
    return max_streak, username


def get_longest_loss_streak(db: Session) -> Optional[Tuple[int, str]]:
    """
    Получает самый долгий стрик поражений (количество поражений подряд).
    
    :param db: Сессия SQLAlchemy
    :return: Кортеж (количество поражений, username) или None
    """
    # Получаем все игры со статусом 'normal', отсортированные по времени
    games = db.query(Match).filter(
        and_(
            Match.result == 'normal',
            Match.ended_at.isnot(None),
            Match.winner_id.isnot(None)
        )
    ).order_by(Match.ended_at.asc()).all()
    
    if not games:
        return None
    
    # Группируем игры по игрокам
    player_games = {}
    for game in games:
        # Добавляем игру для обоих игроков
        for player_id in [game.player_1_id, game.player_2_id]:
            if player_id not in player_games:
                player_games[player_id] = []
            player_games[player_id].append(game)
    
    max_streak = 0
    best_player_id = None
    
    # Для каждого игрока ищем самый длинный стрик поражений
    for player_id, player_games_list in player_games.items():
        current_streak = 0
        max_current_streak = 0
        
        for game in player_games_list:
            # Проверяем, проиграл ли игрок в этой игре
            if game.winner_id != player_id:
                current_streak += 1
                max_current_streak = max(max_current_streak, current_streak)
            else:
                current_streak = 0
        
        if max_current_streak > max_streak:
            max_streak = max_current_streak
            best_player_id = player_id
    
    if best_player_id is None:
        return None
    
    # Получаем username игрока по telegram_id
    player = db.query(Player).filter(Player.telegram_id == str(best_player_id)).first()
    username = player.username if player and player.username else "Неизвестный игрок"
    
    return max_streak, username


def get_most_played_player(db: Session) -> Optional[Tuple[int, str]]:
    """
    Получает игрока с наибольшим количеством сыгранных игр.
    
    :param db: Сессия SQLAlchemy
    :return: Кортеж (количество игр, username) или None
    """
    # Подсчитываем игры для каждого игрока
    player1_games = db.query(
        Match.player_1_id,
        func.count(Match.id).label('game_count')
    ).filter(
        and_(
            Match.result == 'normal',
            Match.ended_at.isnot(None)
        )
    ).group_by(Match.player_1_id).subquery()
    
    player2_games = db.query(
        Match.player_2_id,
        func.count(Match.id).label('game_count')
    ).filter(
        and_(
            Match.result == 'normal',
            Match.ended_at.isnot(None)
        )
    ).group_by(Match.player_2_id).subquery()
    
    # Объединяем результаты
    total_games = db.query(
        func.coalesce(player1_games.c.player_1_id, player2_games.c.player_2_id).label('player_id'),
        (func.coalesce(player1_games.c.game_count, 0) + func.coalesce(player2_games.c.game_count, 0)).label('total_games')
    ).outerjoin(
        player2_games, player1_games.c.player_1_id == player2_games.c.player_2_id
    ).order_by(desc('total_games')).first()
    
    if not total_games or total_games.total_games == 0:
        return None
    
    # Получаем username игрока по telegram_id
    player = db.query(Player).filter(Player.telegram_id == str(total_games.player_id)).first()
    username = player.username if player and player.username else "Неизвестный игрок"
    
    return total_games.total_games, username


def get_most_time_played_player(db: Session) -> Optional[Tuple[float, str]]:
    """
    Получает игрока с наибольшим суммарным временем игр.
    
    :param db: Сессия SQLAlchemy
    :return: Кортеж (суммарное время в минутах, username) или None
    """
    # Получаем все игры со статусом 'normal' и с завершенным временем
    matches = db.query(Match).filter(
        and_(
            Match.result == 'normal',
            Match.ended_at.isnot(None)
        )
    ).all()
    
    if not matches:
        return None
    
    # Считаем суммарное время для каждого игрока
    player_times = {}
    
    for match in matches:
        try:
            # Проверяем, что это объекты datetime
            if isinstance(match.started_at, str):
                started_at = datetime.fromisoformat(match.started_at.replace('Z', '+00:00'))
            else:
                started_at = match.started_at
                
            if isinstance(match.ended_at, str):
                ended_at = datetime.fromisoformat(match.ended_at.replace('Z', '+00:00'))
            else:
                ended_at = match.ended_at
            
            duration = ended_at - started_at
            
            # Добавляем время для обоих игроков
            for player_id in [match.player_1_id, match.player_2_id]:
                if player_id not in player_times:
                    player_times[player_id] = timedelta(0)
                player_times[player_id] += duration
                
        except (ValueError, TypeError) as e:
            # Пропускаем игры с некорректными датами
            continue
    
    if not player_times:
        return None
    
    # Находим игрока с максимальным временем
    max_time_player = max(player_times.items(), key=lambda x: x[1])
    player_id, total_duration = max_time_player
    
    # Конвертируем в минуты
    total_minutes = int(total_duration.total_seconds() // 60)
    
    # Получаем username игрока по telegram_id
    player = db.query(Player).filter(Player.telegram_id == str(player_id)).first()
    username = player.username if player and player.username else "Неизвестный игрок"
    
    return total_minutes, username
