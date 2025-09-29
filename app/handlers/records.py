from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from datetime import datetime

from app.keyboards import back_to_main_menu
from app.logger import setup_logger
from app.messages.texts import GAME_RECORDS_HEADER, NO_RECORDS_MESSAGE
from app.dependencies import db_session
from app.db_utils.records import (
    get_fastest_game,
    get_longest_win_streak,
    get_longest_loss_streak,
    get_most_played_player,
    get_most_time_played_player
)

logger = setup_logger(__name__)


def format_duration(seconds: float) -> str:
    """Форматирует время в читаемый вид."""
    if seconds < 60:
        return f"{seconds:.0f} сек"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} мин"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} ч"


async def show_records_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает callback-запрос на отображение рекордов игры.
    - Логирует запрос пользователя.
    - Получает рекорды из базы данных.
    - Отправляет текст с рекордами.

    :param callback: Объект callback-запроса от пользователя.
    """
    logger.info(f"🎖️ Игрок @{callback.from_user.username} запросил рекорды игры!")
    try:
        await callback.answer()
    except Exception:
        pass
    
    try:
        with db_session() as db:
            # Получаем все рекорды
            fastest_game = get_fastest_game(db)
            win_streak = get_longest_win_streak(db)
            loss_streak = get_longest_loss_streak(db)
            most_games = get_most_played_player(db)
            most_time = get_most_time_played_player(db)
            
            # Проверяем, есть ли хотя бы один рекорд
            has_records = any([fastest_game, win_streak, loss_streak, most_games, most_time])
            
            if not has_records:
                await callback.message.edit_text(
                    GAME_RECORDS_HEADER + NO_RECORDS_MESSAGE,
                    parse_mode="HTML",
                    reply_markup=back_to_main_menu()
                )
                return
            
            # Формируем текст с рекордами
            records_text = GAME_RECORDS_HEADER
            
            # Самая быстрая игра
            if fastest_game:
                match, player1, player2 = fastest_game
                try:
                    # Обрабатываем случаи, когда даты могут быть строками
                    if isinstance(match.started_at, str):
                        started_at = datetime.fromisoformat(match.started_at.replace('Z', '+00:00'))
                    else:
                        started_at = match.started_at
                        
                    if isinstance(match.ended_at, str):
                        ended_at = datetime.fromisoformat(match.ended_at.replace('Z', '+00:00'))
                    else:
                        ended_at = match.ended_at
                    
                    duration_seconds = (ended_at - started_at).total_seconds()
                    fastest_date = ended_at.strftime("%d.%m.%Y в %H:%M")
                    
                    records_text += f"⚡ <b>Самая быстрая игра:</b>\n"
                    records_text += f"⏱️ Время: {int(duration_seconds)} сек.\n"
                    records_text += f"📅 Дата: {fastest_date}\n"
                    records_text += f"👥 Игроки: @{player1} vs @{player2}\n\n"
                except (ValueError, TypeError) as e:
                    records_text += "⚡ <b>Самая быстрая игра:</b>\n❌ Ошибка обработки данных\n\n"
            else:
                records_text += "⚡ <b>Самая быстрая игра:</b>\n❌ Нет данных\n\n"
            
            # Самый долгий стрик побед
            if win_streak:
                streak_count, player = win_streak
                records_text += f"🔥 <b>Самый долгий стрик побед:</b>\n"
                records_text += f"🏆 @{player} — {streak_count} побед подряд\n\n"
            else:
                records_text += "🔥 <b>Самый долгий стрик побед:</b>\n❌ Нет данных\n\n"
            
            # Самый долгий стрик поражений
            if loss_streak:
                streak_count, player = loss_streak
                records_text += f"💥 <b>Самый долгий стрик поражений:</b>\n"
                records_text += f"😔 @{player} — {streak_count} поражений подряд\n\n"
            else:
                records_text += "💥 <b>Самый долгий стрик поражений:</b>\n❌ Нет данных\n\n"
            
            # Самый играющий игрок (по количеству игр)
            if most_games:
                games_count, player = most_games
                records_text += f"🎮 <b>Самый играющий игрок (по количеству игр):</b>\n"
                records_text += f"📊 @{player} — {games_count} игр\n\n"
            else:
                records_text += "🎮 <b>Самый играющий игрок (по количеству игр):</b>\n❌ Нет данных\n\n"
            
            # Самый играющий игрок (по времени)
            if most_time:
                time_minutes, player = most_time
                records_text += f"⏰ <b>Самый играющий игрок (по времени):</b>\n"
                records_text += f"🕐 @{player} — {time_minutes} мин.\n"
            else:
                records_text += "⏰ <b>Самый играющий игрок (по времени):</b>\n❌ Нет данных"
            
            await callback.message.edit_text(
                records_text,
                parse_mode="HTML",
                reply_markup=back_to_main_menu()
            )
            
    except Exception as e:
        logger.error(f"Ошибка при получении рекордов: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке рекордов. Попробуйте позже.",
            parse_mode="HTML",
            reply_markup=back_to_main_menu()
        )


def register_handler(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики команд и кнопок:
    - Callback-обработчики для inline-кнопок

    :param dp: Объект диспетчера aiogram.
    """
    dp.callback_query.register(show_records_callback, lambda c: c.data == "show_records")
