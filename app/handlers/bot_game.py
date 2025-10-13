from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from app.keyboards import bot_difficulty_menu, playing_menu, main_menu
from app.logger import setup_logger
from app.state.in_memory import games
from app.services.bot_game_service import start_bot_game
from app.messages.texts import YOUR_BOARD_TEXT, START_BOT_GAME, STARTING_GAME_ERROR, INVALID_DIFFICULT_MODE
from app.dependencies import db_session
from app.db_utils.donor import is_donor

logger = setup_logger(__name__)


async def play_vs_bot_menu_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает нажатие кнопки для начала игры с ботом.
    Отправляет игроку сообщение с инструкцией и клавиатуру выбора уровня сложности.

    Args:
        callback (CallbackQuery): объект колбэка от нажатия кнопки.

    Returns:
        None
    """
    try:
        await callback.answer()
    except Exception:
        pass

    # Проверяем статус донора
    with db_session() as db:
        donor_status = is_donor(db, callback.from_user.id)
    
    # Выбираем соответствующую клавиатуру
    keyboard = bot_difficulty_menu(is_donor=donor_status)
    
    await callback.message.edit_text(START_BOT_GAME, parse_mode='HTML', reply_markup=keyboard)


async def start_bot_game_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает выбор сложности для игры с ботом.
    1. Проверяет корректность выбранной сложности.
    2. Проверяет, есть ли у игрока уже активная игра.
    3. Создаёт новую игру с ботом через start_bot_game.
    4. Отправляет игроку стартовое поле и клавиатуру для выстрелов.

    Args:
        callback (CallbackQuery): объект колбэка от нажатия кнопки выбора сложности.

    Returns:
        None
    """
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
        "bot_super_hard": "super_hard",
    }.get(callback.data)

    if not difficulty:
        await callback.message.edit_text(INVALID_DIFFICULT_MODE, reply_markup=main_menu())
        return

    # Блокируем запуск новой игры, если пользователь уже участвует в какой-либо игре
    for gid, g in games.items():
        if user_id == g.get("player1") or user_id == g.get("player2"):
            # если это игра с ботом или активная PvP (оба игрока есть) — запрещаем запуск
            if g.get("is_bot_game") or (g.get("player1") and g.get("player2")):
                logger.warning(f"⚠️ Игрок @{username} пытался начать новую игру с ботом, имея активную игру {gid}.")
                await callback.message.edit_text(STARTING_GAME_ERROR, reply_markup=main_menu())
                return

    # Перед стартом игры с ботом удаляем все созданные пользователем PvP-игры без второго игрока
    to_delete = [gid for gid, g in games.items() if g.get("player1") == user_id and not g.get("player2") and not g.get("is_bot_game")]
    for gid in to_delete:
        games.pop(gid, None)

    game_id = start_bot_game(user_id=user_id, username=username, difficulty=difficulty)

    # Отправляем стартовое поле и клавиатуру выстрелов по боту
    await callback.message.edit_text(
        YOUR_BOARD_TEXT.format(
            board=__import__('app.game_logic', fromlist=['print_board']).print_board(
                games[game_id]["boards"][user_id]
            )
        ),
        parse_mode="HTML"
    )

    await callback.bot.send_message(
        user_id,
        "🎯 Стреляйте по полю соперника!",
        reply_markup=playing_menu(game_id, games[game_id]["bot_id"])
    )


def register_handler(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики колбэков для кнопок игры с ботом:
    - play_vs_bot_menu_callback — для открытия меню выбора сложности.
    - start_bot_game_callback — для запуска игры после выбора сложности.

    Args:
        dp (Dispatcher): объект диспетчера Aiogram.

    Returns:
        None
    """
    dp.callback_query.register(play_vs_bot_menu_callback, lambda c: c.data == "play_vs_bot")
    dp.callback_query.register(start_bot_game_callback, lambda c: c.data in {"bot_easy", "bot_medium", "bot_hard", "bot_super_hard"})
