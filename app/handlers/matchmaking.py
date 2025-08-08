from aiogram import Dispatcher
from aiogram.types import Message, ReplyKeyboardRemove
import asyncio

from app.services.matchmaking_service import try_create_game, try_join_game
from app.game_logic import print_board
from app.keyboards import connect_menu, playing_menu, current_game_menu
from app.storage import user_game_requests, games
from app.logger import setup_logger

from app.messages.texts import (
    STARTING_GAME, STARTING_GAME_ERROR, CHOOSE_CONNECTING_GAME, JOIN_CONNECTING_GAME_ERROR,
    CREATE_GAME_ERROR_MESSAGE, GAME_NOT_FOUND, INVALID_GAME_DATA, SUCCESSFULLY_JOINED,
    PLAYER1_GAME_START, PLAYER2_GAME_START, YOUR_BOARD_TEXT
)
from app.messages.logs import (
    PLAYER_CREATED_GAME, PLAYER_TRIED_CREATE_GAME_AGAIN, PLAYER_CREATE_GAME_ERROR,
    PLAYER_TRIED_JOIN_SAME_GAME, PLAYER_JOINED_GAME
)

logger = setup_logger(__name__)


async def remove_game_if_no_join(game_id: str, delay: int = 300) -> None:
    # Автоудаление игры через delay секунд, если не присоединился 2-й игрок
    await asyncio.sleep(delay)
    game = games.get(game_id)
    if game and game["player2"] is None:
        logger.info(f"🧹 Автоудаление игры {game_id} — второй игрок не присоединился.")
        # Чистим запросы и игру
        for pid in [game["player1"]]:
            if pid in user_game_requests:
                user_game_requests.pop(pid, None)
        games.pop(game_id, None)


async def create_game_command(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    # Проверяем, что игрок не в игре
    if not any(user_id == games[g]["player1"] or user_id == games[g]["player2"] for g in games):
        try:
            game_id = try_create_game(user_id, username)
        except Exception as e:
            logger.error(PLAYER_CREATE_GAME_ERROR.format(username=username, error=e))
            await message.answer(CREATE_GAME_ERROR_MESSAGE)
            return

        logger.info(PLAYER_CREATED_GAME.format(username=username, game_id=game_id))
        user_game_requests[user_id] = None  # Помечаем, что игрок создал игру и ждет подключения второго

        # Запускаем таск автоудаления игры через 5 минут
        asyncio.create_task(remove_game_if_no_join(game_id))

        await message.answer(STARTING_GAME.format(game_id=game_id), reply_markup=connect_menu())
    else:
        logger.warning(PLAYER_TRIED_CREATE_GAME_AGAIN.format(username=username))
        await message.answer(STARTING_GAME_ERROR)


async def process_game_id(message: Message):
    user_game_requests[message.from_user.id] = None
    await message.answer(CHOOSE_CONNECTING_GAME, reply_markup=current_game_menu())


async def join_game_command(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    game_id = message.text

    result = try_join_game(game_id, user_id, username)

    if result == "same_game":
        logger.warning(PLAYER_TRIED_JOIN_SAME_GAME.format(username=username, game_id=game_id))
        await message.answer(JOIN_CONNECTING_GAME_ERROR, reply_markup=current_game_menu())

    elif result == "not_found":
        await message.answer(GAME_NOT_FOUND.format(game_id=game_id))

    elif result == "invalid":
        await message.answer(INVALID_GAME_DATA)

    elif isinstance(result, dict) and result.get("status") == "joined":
        user_game_requests.pop(user_id, None)
        player1 = result["player1"]
        player2 = result["player2"]

        logger.info(PLAYER_JOINED_GAME.format(username=username, game_id=game_id))
        await message.answer(SUCCESSFULLY_JOINED.format(game_id=game_id))
        await message.bot.send_message(player1, PLAYER1_GAME_START.format(username=username),
                                       reply_markup=ReplyKeyboardRemove())
        await message.bot.send_message(player2, PLAYER2_GAME_START.format(username='XXXXXX'),
                                       reply_markup=ReplyKeyboardRemove())

        # Отправляем сообщение игроку 1 и сохраняем message_id
        msg1 = await message.bot.send_message(
            player1,
            YOUR_BOARD_TEXT.format(board=print_board(games[game_id]["boards"][player1])),
            parse_mode="html",
            reply_markup=playing_menu(game_id, player2)
        )

        # Отправляем сообщение игроку 2 и сохраняем message_id
        msg2 = await message.bot.send_message(
            player2,
            YOUR_BOARD_TEXT.format(board=print_board(games[game_id]["boards"][player2])),
            parse_mode="html",
            reply_markup=playing_menu(game_id, player1)
        )

        # Сохраняем ID сообщений в память
        games[game_id]["message_ids"] = {
            player1: msg1.message_id,
            player2: msg2.message_id,
        }


def register_handler(dp: Dispatcher):
    dp.message.register(create_game_command, lambda m: m.text == "🚀 Новая игра")
    dp.message.register(process_game_id, lambda m: m.text in ("📎 Присоединиться к игре", "🔃 Обновить список игр"))
    dp.message.register(join_game_command, lambda m: m.text and m.text.isalnum() and len(m.text) == 6)
