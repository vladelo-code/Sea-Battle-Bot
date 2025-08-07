from aiogram import Dispatcher, types

from app.keyboards import main_menu, connect_menu, playing_menu, current_game_menu, rating_menu
from app.logger import setup_logger

from app.db_utils.stats import update_stats_after_match, get_stats, get_top_players
from app.db_utils.player import get_or_create_player, get_player_by_telegram_id
from app.dependencies import get_db
from app.messages.texts import ELO_INFO

# Инициализация логгера
logger = setup_logger(__name__)


async def stats_command(message: types.Message):
    db_gen = get_db()
    db = next(db_gen)
    try:
        player = get_player_by_telegram_id(db, str(message.from_user.id))
        if not player:
            logger.info(f'🚀 Игрок @{message.from_user.username} пытался получить статистику, будучи не авторизованным.')
            await message.answer("❗ Вы ещё не зарегистрированы в системе.")
            return

        stats = get_stats(db, message.from_user.id)
        if stats:
            logger.info(f'🚀 Игрок @{message.from_user.username} получил свою статистику.')
            await message.answer(
                f"📊 Ваша статистика:\n\n"
                f"🎮 Сыграно матчей: {stats.games_played}\n"
                f"🏆 Побед: {stats.wins}\n"
                f"💥 Поражений: {stats.losses}\n"
                f"📈 Рейтинг: {stats.rating}"
            )
        else:
            logger.info(f'🚀 Игрок @{message.from_user.username} пытался получить статистику, ни разу не сыграв.')
            await message.answer("🤔 У вас пока нет статистики. Сыграйте первую игру!")
    finally:
        db_gen.close()


async def leaderboard_command(message: types.Message):
    db_gen = get_db()
    db = next(db_gen)
    try:
        top_players = get_top_players(db)

        if not top_players:
            logger.info(f'🚀 Игрок @{message.from_user.username} пытался получить рейтинг, но он пуст.')
            await message.answer("😔 Рейтинг пока пуст.")
            return

        text = "🥇 Топ игроков по рейтингу:\n\n"
        for i, (username, rating) in enumerate(top_players, 1):
            name = f"@{username}" if username else "Без имени"
            text += f"{i}. {name} — {rating} 🏆\n"

        logger.info(f'🚀 Игрок @{message.from_user.username} получил рейтинг игроков.')
        await message.answer(text, reply_markup=rating_menu())
    finally:
        db_gen.close()


async def get_elo_explanation(message: types.Message):
    logger.info(f'🚀 Игрок @{message.from_user.username} посмотрел правила начисления рейтинга.')
    await message.answer(ELO_INFO, parse_mode="html", reply_markup=main_menu())


def register_handler(dp: Dispatcher):
    # Вызываем функцию получения статистики '👤 Мой профиль'
    dp.message.register(stats_command, lambda message: message.text == "👤 Мой профиль")

    # Вызываем функцию получения рейтинга '🥇 Рейтинг'
    dp.message.register(leaderboard_command, lambda message: message.text == "🥇 Рейтинг")

    # Вызываем функцию получения информации о рейтинге 'ℹ️ О рейтинге'
    dp.message.register(get_elo_explanation, lambda message: message.text == "ℹ️ О рейтинге")
