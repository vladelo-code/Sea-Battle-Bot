from aiogram import Dispatcher
from aiogram.types import Message

from app.keyboards import main_menu, rating_menu
from app.logger import setup_logger
from app.db_utils.stats import get_stats, get_top_and_bottom_players
from app.db_utils.player import get_player_by_telegram_id
from app.dependencies import db_session

from app.messages.texts import (
    STATS_HEADER,
    STATS_TEMPLATE,
    NO_STATS_MESSAGE,
    NOT_REGISTERED_MESSAGE,
    EMPTY_LEADERBOARD_MESSAGE,
    LEADERBOARD_HEADER,
    LEADERBOARD_ROW,
    UNKNOWN_USERNAME_FIRST,
    ELO_INFO,
)

logger = setup_logger(__name__)


async def stats_command(message: Message) -> None:
    """
    Обрабатывает команду показа статистики игрока.
    Проверяет регистрацию и наличие статистики, отправляет результат или соответствующее сообщение.

    :param message: Сообщение от пользователя Message.
    """
    username = message.from_user.username
    with db_session() as db:
        player = get_player_by_telegram_id(db, str(message.from_user.id))
        if not player:
            logger.info(f"📊 Игрок @{username} пытался получить статистику, будучи не авторизованным.")
            await message.answer(NOT_REGISTERED_MESSAGE)
            return

        stats = get_stats(db, message.from_user.id)
        if not stats:
            logger.info(f"📊 Игрок @{username} пытался получить статистику, ни разу не сыграв.")
            await message.answer(NO_STATS_MESSAGE)
            return

        logger.info(f"📊 Игрок @{username} получил свою статистику.")
        await message.answer(
            STATS_HEADER + STATS_TEMPLATE.format(
                games_played=stats.games_played,
                wins=stats.wins,
                losses=stats.losses,
                rating=stats.rating,
            ),
            parse_mode='HTML',
        )


async def leaderboard_command(message: Message) -> None:
    """
    Обрабатывает команду показа топ-лидера рейтинга.
    Получает топ игроков из БД и формирует сообщение с рейтингом.

    :param message: Сообщение от пользователя Message.
    """
    username = message.from_user.username
    with db_session() as db:
        top_players, bottom_players, total_players = get_top_and_bottom_players(db)

        if not top_players:
            logger.info(f"🥇 Игрок @{username} пытался получить рейтинг, но он пуст.")
            await message.answer(EMPTY_LEADERBOARD_MESSAGE)
            return

        text = LEADERBOARD_HEADER
        for i, (player_username, rating) in enumerate(top_players, 1):
            name = f"@{player_username}" if player_username else UNKNOWN_USERNAME_FIRST
            text += LEADERBOARD_ROW.format(index=i, username=name, rating=rating)

        text += "...\n"
        start_index = total_players - len(bottom_players) + 1
        for i, (player_username, rating) in enumerate(bottom_players, start_index):
            name = f"@{player_username}" if player_username else UNKNOWN_USERNAME_FIRST
            text += LEADERBOARD_ROW.format(index=i, username=name, rating=rating)

        logger.info(f"🥇 Игрок @{username} получил рейтинг игроков.")
        await message.answer(text, parse_mode='html', reply_markup=rating_menu())


async def get_elo_explanation(message: Message) -> None:
    """
    Обрабатывает команду показа информации о рейтинговой системе Elo.

    :param message: Сообщение от пользователя Message.
    """
    username = message.from_user.username
    logger.info(f"ℹ️ Игрок @{username} посмотрел правила начисления рейтинга.")
    await message.answer(ELO_INFO, parse_mode="html", reply_markup=main_menu())


def register_handler(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики сообщений для статистики, рейтинга и объяснения Elo.

    :param dp: Экземпляр Dispatcher из aiogram.
    """
    # Вызываем функцию получения статистики '👤 Мой профиль'
    dp.message.register(stats_command, lambda message: message.text == "👤 Мой профиль")

    # Вызываем функцию получения рейтинга '🥇 Рейтинг'
    dp.message.register(leaderboard_command, lambda message: message.text == "🥇 Рейтинг")

    # Вызываем функцию получения информации о рейтинге 'ℹ️ О рейтинге'
    dp.message.register(get_elo_explanation, lambda message: message.text == "ℹ️ О рейтинге")
