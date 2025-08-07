from aiogram import Dispatcher
from aiogram.types import Message

from app.keyboards import main_menu, rating_menu
from app.logger import setup_logger

from app.db_utils.stats import get_stats, get_top_players
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
    UNKNOWN_USERNAME,
    ELO_INFO,
)

from app.messages.logs import (
    PLAYER_STATS_SUCCESS,
    PLAYER_STATS_NO_GAMES,
    PLAYER_STATS_UNREGISTERED,
    PLAYER_LEADERBOARD_EMPTY,
    PLAYER_LEADERBOARD_SUCCESS,
    PLAYER_ELO_INFO_VIEWED,
)

# Инициализация логгера
logger = setup_logger(__name__)


async def stats_command(message: Message):
    username = message.from_user.username
    with db_session() as db:
        player = get_player_by_telegram_id(db, str(message.from_user.id))
        if not player:
            logger.info(PLAYER_STATS_UNREGISTERED.format(username=username))
            await message.answer(NOT_REGISTERED_MESSAGE)
            return

        stats = get_stats(db, message.from_user.id)
        if not stats:
            logger.info(PLAYER_STATS_NO_GAMES.format(username=username))
            await message.answer(NO_STATS_MESSAGE)
            return

        logger.info(PLAYER_STATS_SUCCESS.format(username=username))
        await message.answer(
            STATS_HEADER + STATS_TEMPLATE.format(
                games_played=stats.games_played,
                wins=stats.wins,
                losses=stats.losses,
                rating=stats.rating,
            )
        )


async def leaderboard_command(message: Message):
    username = message.from_user.username
    with db_session() as db:
        top_players = get_top_players(db)

        if not top_players:
            logger.info(PLAYER_LEADERBOARD_EMPTY.format(username=username))
            await message.answer(EMPTY_LEADERBOARD_MESSAGE)
            return

        text = LEADERBOARD_HEADER
        for i, (player_username, rating) in enumerate(top_players, 1):
            name = f"@{player_username}" if player_username else UNKNOWN_USERNAME
            text += LEADERBOARD_ROW.format(index=i, username=name, rating=rating)

        logger.info(PLAYER_LEADERBOARD_SUCCESS.format(username=username))
        await message.answer(text, reply_markup=rating_menu())


async def get_elo_explanation(message: Message):
    username = message.from_user.username
    logger.info(PLAYER_ELO_INFO_VIEWED.format(username=username))
    await message.answer(ELO_INFO, parse_mode="html", reply_markup=main_menu())


def register_handler(dp: Dispatcher):
    # Вызываем функцию получения статистики '👤 Мой профиль'
    dp.message.register(stats_command, lambda message: message.text == "👤 Мой профиль")

    # Вызываем функцию получения рейтинга '🥇 Рейтинг'
    dp.message.register(leaderboard_command, lambda message: message.text == "🥇 Рейтинг")

    # Вызываем функцию получения информации о рейтинге 'ℹ️ О рейтинге'
    dp.message.register(get_elo_explanation, lambda message: message.text == "ℹ️ О рейтинге")
