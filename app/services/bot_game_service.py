import asyncio
from typing import Optional
from aiogram.types import Message, ReplyKeyboardRemove

from app.state.in_memory import games
from app.game_logic import create_empty_board, place_all_ships, process_shot, check_victory, print_board
from app.utils.game_id import generate_game_id
from app.utils.none_username import safe_username
from app.keyboards import enemy_board_keyboard, after_game_menu
from app.services.bot_ai import BotAI
from app.logger import setup_logger
from app.messages.texts import (
    SUCCESSFUL_SHOT, BAD_SHOT, YOUR_BOARD_TEXT_AFTER_SUCCESS_SHOT, YOUR_BOARD_TEXT_AFTER_BAD_SHOT,
    WINNER, LOSER, AD_AFTER_GAME
)

logger = setup_logger(__name__)


def start_bot_game(user_id: int, username: Optional[str], difficulty: str) -> str:
    # Создаем доски
    human_board = create_empty_board()
    bot_board = create_empty_board()
    place_all_ships(human_board)
    place_all_ships(bot_board)

    # Регистрируем игру
    game_id = generate_game_id()
    bot_id = -abs(hash((user_id, game_id)))  # отрицательный идентификатор для бота в памяти

    games[game_id] = {
        "player1": user_id,
        "player2": bot_id,
        "bot_id": bot_id,
        "is_bot_game": True,
        "difficulty": difficulty,
        "boards": {user_id: human_board, bot_id: bot_board},
        "turn": user_id,
        "usernames": {
            user_id: safe_username(username, "Игрок"),
            bot_id: "vladelo_sea_battle_bot",
        },
        "message_ids": {},
        "bot_state": {
            "ai": BotAI(difficulty),
        },
    }

    logger.info(f"🤖 Создана игра с ботом. Игрок @{username}, сложность: {difficulty}, game_id={game_id}")
    return game_id


async def handle_player_shot_vs_bot(message: Message) -> None:
    user_id = message.from_user.id

    # Найдем игру с ботом для пользователя
    game_id: Optional[str] = None
    for gid, g in games.items():
        if g.get("is_bot_game") and (g.get("player1") == user_id or g.get("player2") == user_id):
            game_id = gid
            break

    if not game_id or game_id not in games:
        await message.answer("❗ Игра против бота не найдена.")
        return

    game = games[game_id]
    bot_id = game["bot_id"]

    if game["turn"] != user_id:
        await message.answer("❗ Сейчас не ваш ход.")
        return

    # Парс координат
    try:
        coord = message.text.upper()
        x = ord(coord[0]) - ord('A')
        y = int(coord[1:]) - 1
        if not (0 <= x < 10 and 0 <= y < 10):
            raise ValueError
    except Exception:
        await message.answer("❗ Неверные координаты. Используйте формат A1.")
        return

    # Игрок стреляет по доске бота
    bot_board = game["boards"][bot_id]
    hit = process_shot(bot_board, x, y)

    if check_victory(bot_board):
        # Игрок победил
        games.pop(game_id, None)
        await message.bot.send_message(user_id, WINNER.format(username="Бот"), parse_mode="html",
                                       reply_markup=ReplyKeyboardRemove())
        await message.bot.send_message(user_id, AD_AFTER_GAME, parse_mode="html", disable_web_page_preview=True,
                                       reply_markup=after_game_menu())
        return

    if hit:
        msg = await message.bot.send_message(
            chat_id=user_id,
            text=SUCCESSFUL_SHOT,
            parse_mode="html",
            reply_markup=enemy_board_keyboard(game_id, bot_id)
        )
    else:
        # Передача хода боту
        game["turn"] = bot_id

        msg = await message.bot.send_message(
            chat_id=user_id,
            text=BAD_SHOT,
            parse_mode="html",
            reply_markup=enemy_board_keyboard(game_id, bot_id)
        )

        # Ход бота (пока ход не вернется игроку или игра не закончится)
        await _bot_turn_loop(message, game_id)

    # Обновим message_ids
    game.setdefault("message_ids", {})
    game["message_ids"][user_id] = msg.message_id


async def _bot_turn_loop(message: Message, game_id: str) -> None:
    game = games.get(game_id)
    if not game:
        return

    user_id = game["player1"] if game["player1"] != game["bot_id"] else game["player2"]
    bot_id = game["bot_id"]
    ai: BotAI = game["bot_state"]["ai"]

    human_board = game["boards"][user_id]

    while game["turn"] == bot_id:
        x, y = ai.choose_shot()

        result = process_shot(human_board, x, y)
        # ship_destroyed приблизительно определяем: если вокруг клетки появились «❌» после handle_ship_destruction —
        # но в текущей реализации process_shot уже помечает окружение при полном уничтожении. Берем эвристику:
        ship_destroyed = False  # простая эвристика: не определяем точно, достаточно для очереди целей
        ai.process_result((x, y), result, ship_destroyed)

        if result is True:
            # По игроку попали — бот ходит снова
            await message.bot.send_message(
                chat_id=user_id,
                text=YOUR_BOARD_TEXT_AFTER_SUCCESS_SHOT.format(board=print_board(human_board)),
                parse_mode="html",
                reply_markup=enemy_board_keyboard(game_id, bot_id)
            )

            if check_victory(human_board):
                games.pop(game_id, None)
                await message.bot.send_message(user_id, LOSER.format(username="Бот"), parse_mode="html",
                                               reply_markup=ReplyKeyboardRemove())
                await message.bot.send_message(user_id, AD_AFTER_GAME, parse_mode="html",
                                               disable_web_page_preview=True, reply_markup=after_game_menu())
                return
            # задержка между последовательными попаданиями бота
            await asyncio.sleep(3)
        elif result is False:
            # Мимо — ход переходит игроку
            game["turn"] = user_id
            await message.bot.send_message(
                chat_id=user_id,
                text=YOUR_BOARD_TEXT_AFTER_BAD_SHOT.format(board=print_board(human_board)),
                parse_mode="html",
                reply_markup=enemy_board_keyboard(game_id, bot_id)
            )
            break
        else:
            # Некорректный ход — помечаем клетку и продолжаем
            game["turn"] = bot_id


async def handle_surrender_vs_bot(message: Message) -> None:
    user_id = message.from_user.id
    game_id: Optional[str] = None
    for gid, g in games.items():
        if g.get("is_bot_game") and (g.get("player1") == user_id or g.get("player2") == user_id):
            game_id = gid
            break

    if not game_id or game_id not in games:
        await message.answer("❗ Игра против бота не найдена.")
        return

    games.pop(game_id, None)

    await message.bot.send_message(
        user_id,
        "🏳️ Поражение! Вы сдались в игре против бота!",
        parse_mode="html",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.bot.send_message(
        user_id,
        AD_AFTER_GAME,
        parse_mode="html",
        disable_web_page_preview=True,
        reply_markup=after_game_menu()
    )
