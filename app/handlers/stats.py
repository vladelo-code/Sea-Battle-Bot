from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from app.keyboards import rating_menu, back_to_main_menu, profile_menu
from app.logger import setup_logger
from app.db_utils.stats import get_top_and_bottom_players
from app.db_utils.player import get_player_by_telegram_id, get_extended_stats
from app.dependencies import db_session

from app.messages.texts import (
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


async def stats_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает callback-запрос показа статистики игрока.
    Проверяет регистрацию и наличие статистики, отправляет результат или соответствующее сообщение.

    :param callback: Callback-запрос от пользователя.
    """
    try:
        await callback.answer()
    except Exception:
        pass

    username = callback.from_user.username
    with db_session() as db:
        player = get_player_by_telegram_id(db, str(callback.from_user.id))
        if not player:
            logger.info(f"📊 Игрок @{username} пытался получить статистику, будучи не авторизованным.")
            await callback.message.edit_text(NOT_REGISTERED_MESSAGE, reply_markup=back_to_main_menu())
            return

        stats = get_extended_stats(db, str(callback.from_user.id))
        if not stats:
            logger.info(f"📊 Игрок @{username} пытался получить статистику, ни разу не сыграв.")
            await callback.message.edit_text(NO_STATS_MESSAGE, reply_markup=back_to_main_menu())
            return

        logger.info(f"📊 Игрок @{username} получил свою статистику.")

        await callback.message.edit_text(
            STATS_TEMPLATE.format(
                donor='открыты' if stats.get("is_donor", False) else 'закрыты',
                games_played=stats["games_played"],
                wins=stats["wins"],
                losses=stats["losses"],
                rating=stats["rating"],
                place=stats["place"],
                total_players=stats["total_players"],
                first_seen=stats["first_seen"].strftime("%d.%m.%Y"),
                avg_time=int(stats["avg_time"] // 60),
                total_time=int(stats["total_time"] // 60),
            ),
            parse_mode='HTML',
            reply_markup=profile_menu()
        )


async def leaderboard_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает callback-запрос показа топ-лидера рейтинга.
    Получает топ игроков из БД и формирует сообщение с рейтингом.
    Если текущий пользователь не входит в топ, показывает его позицию.

    :param callback: Callback-запрос от пользователя.
    """
    try:
        await callback.answer()
    except Exception:
        pass

    username = callback.from_user.username
    with db_session() as db:
        top_players, bottom_players, total_players, current_user_position = get_top_and_bottom_players(
            db, current_user_id=str(callback.from_user.id)
        )

        if not top_players:
            logger.info(f"🥇 Игрок @{username} пытался получить рейтинг, но он пуст.")
            await callback.message.edit_text(EMPTY_LEADERBOARD_MESSAGE, reply_markup=back_to_main_menu())
            return

        text = LEADERBOARD_HEADER
        for i, (player_username, rating, _, is_donor) in enumerate(top_players, 1):
            donor_badge = "💎" if is_donor else ""
            name = f"@{player_username}" if player_username else UNKNOWN_USERNAME_FIRST
            name_with_badge = f"{donor_badge} {name}".strip()
            text += LEADERBOARD_ROW.format(index=i, username=name_with_badge, rating=rating)

        # Если пользователь не в топе, добавляем его позицию
        if current_user_position:
            user_username, user_rating, user_position, user_is_donor = current_user_position
            donor_badge = "💎" if user_is_donor else ""
            name = f"@{user_username}" if user_username else UNKNOWN_USERNAME_FIRST
            name_with_badge = f"{donor_badge} {name}".strip()
            text += "...\n"
            text += LEADERBOARD_ROW.format(index=user_position, username=name_with_badge, rating=user_rating)
            text += "...\n"
        else:
            text += "...\n"

        start_index = total_players - len(bottom_players) + 1
        for i, (player_username, rating, _, is_donor) in enumerate(bottom_players, start_index):
            donor_badge = "💎" if is_donor else ""
            name = f"@{player_username}" if player_username else UNKNOWN_USERNAME_FIRST
            name_with_badge = f"{donor_badge} {name}".strip()
            text += LEADERBOARD_ROW.format(index=i, username=name_with_badge, rating=rating)

        # text += LEADERBOARD_FOOTER.format(total_players=total_players)

        logger.info(f"🥇 Игрок @{username} получил рейтинг игроков.")
        await callback.message.edit_text(text, parse_mode='html', reply_markup=rating_menu())


async def get_elo_explanation_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает callback-запрос показа информации о рейтинговой системе Elo.

    :param callback: Callback-запрос от пользователя.
    """
    try:
        await callback.answer()
    except Exception:
        pass

    username = callback.from_user.username
    logger.info(f"ℹ️ Игрок @{username} посмотрел правила начисления рейтинга.")
    await callback.message.edit_text(ELO_INFO, parse_mode="html", reply_markup=back_to_main_menu())


def register_handler(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики inline-кнопок для статистики, рейтинга и объяснения Elo.

    :param dp: Экземпляр Dispatcher из aiogram.
    """
    dp.callback_query.register(stats_callback, lambda c: c.data == "my_profile")
    dp.callback_query.register(leaderboard_callback, lambda c: c.data == "rating")
    dp.callback_query.register(get_elo_explanation_callback, lambda c: c.data == "about_rating")
