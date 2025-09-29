from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from app.dependencies import db_session
from app.db_utils.player import get_player_by_telegram_id
from app.db_utils.bot_stats import get_aggregated_bot_stats
from app.keyboards import bot_analytic_menu
from app.messages.texts import (
    BOT_ANALYTICS_TEMPLATE,
    NO_BOT_ANALYTICS,
)
from app.logger import setup_logger

logger = setup_logger(__name__)


async def bot_analytics_callback(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except Exception:
        pass

    with db_session() as db:
        player = get_player_by_telegram_id(db, str(callback.from_user.id))
        if not player:
            await callback.message.edit_text(NO_BOT_ANALYTICS, reply_markup=bot_analytic_menu())
            return

        data = get_aggregated_bot_stats(db, callback.from_user.id)

    if not data or data.get("total_games", 0) == 0:
        await callback.message.edit_text(NO_BOT_ANALYTICS, reply_markup=bot_analytic_menu())
        return

    by_diff = data.get("by_difficulty", {})

    def diff(name: str):
        d = by_diff.get(name, {})
        return d.get("games", 0), d.get("wins", 0), d.get("losses", 0)

    easy_g, easy_w, easy_l = diff("easy")
    med_g, med_w, med_l = diff("medium")
    hard_g, hard_w, hard_l = diff("hard")

    text = (
        BOT_ANALYTICS_TEMPLATE.format(
            total_games=data["total_games"],
            total_wins=data["total_wins"],
            total_losses=data["total_losses"],
            easy_games=easy_g, easy_wins=easy_w, easy_losses=easy_l,
            medium_games=med_g, medium_wins=med_w, medium_losses=med_l,
            hard_games=hard_g, hard_wins=hard_w, hard_losses=hard_l,
        )
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=bot_analytic_menu())


def register_handler(dp: Dispatcher) -> None:
    dp.callback_query.register(bot_analytics_callback, lambda c: c.data == "bot_analytics")
