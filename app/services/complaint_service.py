import asyncio
from typing import Optional
from aiogram import Bot
from aiogram.types import ReplyKeyboardRemove

from app.state.in_memory import games, complaint_timers
from app.keyboards import after_game_menu
from app.db_utils.match import update_match_result
from app.db_utils.stats import update_stats_after_match
from app.dependencies import db_session
from app.services.achievements_service import evaluate_achievements_after_multiplayer_match
from app.logger import setup_logger
from app.messages.texts import (
    COMPLAINT_STARTED, COMPLAINT_NOTIFICATION, COMPLAINT_TIMER_CANCELLED,
    COMPLAINT_AUTO_WIN, COMPLAINT_AUTO_LOSS, COMPLAINT_ALREADY_ACTIVE,
    COMPLAINT_NOT_YOUR_TURN, AD_AFTER_GAME, COMPLAINT_TIMER_CANCELLED_OPPONENT
)

logger = setup_logger(__name__)


async def handle_complaint(bot: Bot, user_id: int) -> bool:
    """
    Обрабатывает жалобу на бездействие игрока.
    
    :param bot: Объект бота для отправки сообщений
    :param user_id: ID игрока, подающего жалобу
    :return: True если жалоба успешно подана, False если есть ошибки
    """
    # Найдем игру, в которой играет user_id
    game_id: Optional[str] = None
    for gid, g in games.items():
        if user_id == g.get("player1") or user_id == g.get("player2"):
            game_id = gid
            break

    if not game_id or game_id not in games:
        return False

    game = games[game_id]

    # Проверяем, что это не игра с ботом
    if game.get("is_bot_game"):
        return False

    # Проверяем, что сейчас не ход жалующегося игрока
    if game["turn"] == user_id:
        await bot.send_message(user_id, COMPLAINT_NOT_YOUR_TURN, parse_mode="HTML")
        return False

    # Проверяем, что жалоба еще не активна
    if game_id in complaint_timers:
        await bot.send_message(user_id, COMPLAINT_ALREADY_ACTIVE, parse_mode="HTML")
        return False

    # Определяем противника
    opponent_id = game["player1"] if user_id == game["player2"] else game["player2"]

    # Получаем username'ы
    usernames = game.get("usernames", {})
    complainer_username = usernames.get(user_id, "Игрок")
    opponent_username = usernames.get(opponent_id, "Противник")

    logger.info(f'⚠️ Игрок @{complainer_username} подал жалобу на @{opponent_username}, ID игры: {game_id}')

    # Отправляем уведомления
    await bot.send_message(user_id, COMPLAINT_STARTED, parse_mode="HTML")
    await bot.send_message(opponent_id, COMPLAINT_NOTIFICATION, parse_mode="HTML")

    # Запускаем таймер
    timer_task = asyncio.create_task(complaint_timer(bot, game_id, user_id, opponent_id))
    complaint_timers[game_id] = timer_task

    return True


async def complaint_timer(bot: Bot, game_id: str, complainer_id: int, opponent_id: int) -> None:
    """
    Таймер жалобы - ждет 5 минут и автоматически завершает игру в пользу жалующегося.
    
    :param bot: Объект бота
    :param game_id: ID игры
    :param complainer_id: ID жалующегося игрока
    :param opponent_id: ID игрока, на которого жалуются
    """
    try:
        # Ждем 5 минут (300 секунд)
        await asyncio.sleep(300)

        # Проверяем, что игра еще существует
        if game_id not in games:
            return

        game = games[game_id]

        # Проверяем, что жалоба все еще активна (игрок не сделал ход)
        if game_id in complaint_timers:
            await auto_win_by_complaint(bot, game_id, complainer_id, opponent_id)

    except asyncio.CancelledError:
        # Таймер был отменен (игрок сделал ход)
        logger.info(f'⏰ Таймер жалобы отменен для игры {game_id}')
    except Exception as e:
        logger.error(f'Ошибка в таймере жалобы для игры {game_id}: {e}')


async def cancel_complaint_timer(game_id: str) -> bool:
    """
    Отменяет таймер жалобы (когда игрок сделал ход).
    :return: True если таймер был активен и отменён, иначе False.
    """
    if game_id in complaint_timers:
        timer_task = complaint_timers.pop(game_id)
        timer_task.cancel()
        return True
    return False


async def notify_complaint_cancelled(bot: Bot, game_id: str, current_player_id: int) -> None:
    """
    Уведомляет жалующегося игрока о том, что жалоба отменена.
    
    :param bot: Объект бота
    :param game_id: ID игры
    :param current_player_id: ID игрока, который только что сделал ход
    """
    if game_id not in games:
        return

    game = games[game_id]
    # Определяем жалующегося игрока (противника того, кто сделал ход)
    complainer_id = game["player1"] if current_player_id == game["player2"] else game["player2"]

    await bot.send_message(complainer_id, COMPLAINT_TIMER_CANCELLED, parse_mode="HTML")
    await bot.send_message(current_player_id, COMPLAINT_TIMER_CANCELLED_OPPONENT, parse_mode="HTML")


async def auto_win_by_complaint(bot: Bot, game_id: str, winner_id: int, loser_id: int) -> None:
    """
    Автоматически завершает игру в пользу жалующегося игрока.
    
    :param bot: Объект бота
    :param game_id: ID игры
    :param winner_id: ID победителя (жалующегося)
    :param loser_id: ID проигравшего
    """
    if game_id not in games:
        return

    game = games[game_id]
    usernames = game.get("usernames", {})
    winner_username = usernames.get(winner_id, "Игрок")
    loser_username = usernames.get(loser_id, "Противник")

    logger.info(f'🏆 Автоматическая победа @{winner_username} по жалобе, ID игры: {game_id}')

    # Обновляем базу данных
    with db_session() as db:
        match = update_match_result(db, game_id, winner_id=winner_id, result="complaint")
        update_stats_after_match(db, winner_id=winner_id, loser_id=loser_id)
        try:
            if match:
                evaluate_achievements_after_multiplayer_match(db, match)
        except Exception:
            pass

    # Получаем доски для отображения
    winner_board = game["boards"].get(winner_id)
    loser_board = game["boards"].get(loser_id)

    # Удаляем игру и таймер
    games.pop(game_id, None)
    complaint_timers.pop(game_id, None)

    # Отправляем сообщения
    await bot.send_message(
        winner_id,
        COMPLAINT_AUTO_WIN,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

    await bot.send_message(
        winner_id,
        text=AD_AFTER_GAME,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=after_game_menu()
    )

    await bot.send_message(
        loser_id,
        COMPLAINT_AUTO_LOSS,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

    await bot.send_message(
        loser_id,
        text=AD_AFTER_GAME,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=after_game_menu()
    )
