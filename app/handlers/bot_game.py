from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from app.keyboards import bot_difficulty_menu, playing_menu, main_menu
from app.logger import setup_logger
from app.state.in_memory import games
from app.services.bot_game_service import start_bot_game
from app.messages.texts import YOUR_BOARD_TEXT


logger = setup_logger(__name__)


async def play_vs_bot_menu_callback(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except Exception:
        pass

    await callback.message.edit_text("🤖 Выберите сложность игры против бота:", reply_markup=bot_difficulty_menu())


async def start_bot_game_callback(callback: CallbackQuery) -> None:
    try:
        await callback.answer()
    except Exception:
        pass

    user_id = callback.from_user.id
    username = callback.from_user.username

    difficulty = {
        "bot_easy": "easy",
        "bot_medium": "medium",
        "bot_hard": "hard",
    }.get(callback.data)

    if not difficulty:
        await callback.message.edit_text("❗ Некорректный режим.", reply_markup=main_menu())
        return

    # Блокируем запуск новой игры, если пользователь уже участвует в какой-либо игре
    for gid, g in games.items():
        if user_id == g.get("player1") or user_id == g.get("player2"):
            # если это игра с ботом или активная PvP (оба игрока есть) — запрещаем запуск
            if g.get("is_bot_game") or (g.get("player1") and g.get("player2")):
                logger.warning(f"⚠️ Игрок @{username} пытался начать новую игру с ботом, имея активную игру {gid}.")
                await callback.message.edit_text("⚠️ У вас уже есть активная игра. Завершите её, прежде чем начинать новую.",
                                                reply_markup=main_menu())
                return

    game_id = start_bot_game(user_id=user_id, username=username, difficulty=difficulty)

    # Отправляем стартовое поле и клавиатуру выстрелов по боту
    await callback.message.edit_text(
        YOUR_BOARD_TEXT.format(board=\
            __import__('app.game_logic', fromlist=['print_board']).print_board(games[game_id]["boards"][user_id])
        ),
        parse_mode="html"
    )

    await callback.bot.send_message(
        user_id,
        "🎯 Стреляйте по полю соперника!",
        reply_markup=playing_menu(game_id, games[game_id]["bot_id"])
    )


def register_handler(dp: Dispatcher) -> None:
    dp.callback_query.register(play_vs_bot_menu_callback, lambda c: c.data == "play_vs_bot")
    dp.callback_query.register(start_bot_game_callback, lambda c: c.data in {"bot_easy", "bot_medium", "bot_hard"})


