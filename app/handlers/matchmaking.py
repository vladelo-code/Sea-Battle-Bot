from aiogram import Dispatcher
from aiogram.types import CallbackQuery, ReplyKeyboardRemove
import asyncio

from app.services.matchmaking_service import try_create_game, try_join_game
from app.game_logic import print_board
from app.keyboards import connect_menu, playing_menu, current_game_menu, main_menu
from app.state.in_memory import user_game_requests, games
from app.utils.game_cleanup import remove_game_if_no_join
from app.logger import setup_logger

from app.messages.texts import (
    STARTING_GAME, STARTING_GAME_ERROR, CHOOSE_CONNECTING_GAME, JOIN_CONNECTING_GAME_ERROR,
    CREATE_GAME_ERROR_MESSAGE, GAME_NOT_FOUND, INVALID_GAME_DATA, SUCCESSFULLY_JOINED,
    PLAYER1_GAME_START, PLAYER2_GAME_START, YOUR_BOARD_TEXT
)

logger = setup_logger(__name__)


async def create_game_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает callback-запрос создания новой игры.
    Проверяет, не участвует ли пользователь уже в другой игре.
    Если нет — создаёт новую игру и запускает таймер автоудаления, если не подключится второй игрок.

    :param callback: Объект callback-запроса от пользователя.
    """
    await callback.answer()
    user_id = callback.from_user.id
    username = callback.from_user.username

    # Проверяем, что игрок не в игре
    if not any(user_id == games[g]["player1"] or user_id == games[g]["player2"] for g in games):
        try:
            game_id = try_create_game(user_id, username)
        except Exception as e:
            logger.error(f"❌ Ошибка при создании игры для @{username}: {e}")
            await callback.message.edit_text(CREATE_GAME_ERROR_MESSAGE, reply_markup=main_menu())
            return

        logger.info(f"🚀 Игрок @{username} создал игру, ID игры: {game_id}")
        user_game_requests[user_id] = None  # Помечаем, что игрок создал игру и ждет подключения второго

        # Запускаем таск автоудаления игры через 5 минут
        asyncio.create_task(remove_game_if_no_join(game_id, callback.bot))

        await callback.message.edit_text(STARTING_GAME.format(game_id=game_id), reply_markup=connect_menu(),
                                         parse_mode="html")

        # Сохраняем message_id сообщения о создании игры для последующего удаления
        games[game_id]["creation_message_id"] = callback.message.message_id
    else:
        logger.warning(f"⚠️ Игрок @{username} пытался создать ещё игру, не закончив предыдущую.")
        await callback.message.edit_text(STARTING_GAME_ERROR, reply_markup=current_game_menu())


async def join_game_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает callback-запрос выбора опции "📎 Присоединиться к игре".
    Предлагает пользователю список активных игр.

    :param callback: Объект callback-запроса от пользователя.
    """
    await callback.answer()
    user_id = callback.from_user.id
    username = callback.from_user.username

    # Проверяем, не играет ли игрок в активной игре (игра началась, есть 2 игрока)
    active_game = None
    for gid, g in games.items():
        if user_id == g.get("player1") or user_id == g.get("player2"):
            # Если игра активна (есть 2 игрока), блокируем присоединение
            if g.get("player1") and g.get("player2"):
                active_game = gid
                break

    if active_game:
        logger.warning(
            f"⚠️ Игрок @{username} пытался присоединиться к игре, уже участвуя в активной игре {active_game}.")
        await callback.message.edit_text(STARTING_GAME_ERROR, reply_markup=current_game_menu())
    else:
        user_game_requests[user_id] = None
        await callback.message.edit_text(CHOOSE_CONNECTING_GAME, reply_markup=current_game_menu())


async def join_game_by_id_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает callback-запрос подключения к игре по ID.
    В случае успеха отправляет стартовые поля обоим игрокам и сохраняет message_id.

    :param callback: Объект callback-запроса от пользователя.
    """
    await callback.answer()
    user_id = callback.from_user.id
    username = callback.from_user.username
    game_id = callback.data.replace("join_game_", "")

    result = try_join_game(game_id, user_id, username)

    if result == "same_game":
        logger.warning(f"⚠️ Игрок @{username} пытался подключиться к своей же игре с ID: {game_id}")
        await callback.message.edit_text(JOIN_CONNECTING_GAME_ERROR, reply_markup=current_game_menu())

    elif result == "not_found":
        await callback.message.edit_text(GAME_NOT_FOUND.format(game_id=game_id), reply_markup=main_menu())

    elif result == "already_in_active_game":
        logger.warning(f"⚠️ Игрок @{username} пытался присоединиться к игре, уже участвуя в активной игре.")
        await callback.message.edit_text(STARTING_GAME_ERROR, reply_markup=current_game_menu())


    elif result == "invalid":
        await callback.message.edit_text(INVALID_GAME_DATA, reply_markup=main_menu())

    elif isinstance(result, dict) and result.get("status") == "joined":
        user_game_requests.pop(user_id, None)
        player1 = result["player1"]
        player2 = result["player2"]
        usernames = games[game_id].get("usernames", {})
        username_player1 = usernames.get(player1, "Игрок 1")
        username_player2 = usernames.get(player2, "Игрок 2")

        logger.info(f"➕ Игрок @{username} присоединился к игре, ID игры: {game_id}")

        # Удаляем сообщение о создании игры у первого игрока
        creation_message_id = games[game_id].get("creation_message_id")
        if creation_message_id:
            try:
                await callback.bot.delete_message(player1, creation_message_id)
            except Exception:
                pass

        await callback.message.edit_text(SUCCESSFULLY_JOINED.format(game_id=game_id))
        await callback.bot.send_message(player1, PLAYER1_GAME_START.format(username=username_player2),
                                        parse_mode="html",
                                        reply_markup=ReplyKeyboardRemove())
        await callback.bot.send_message(player2, PLAYER2_GAME_START.format(username=username_player1),
                                        parse_mode="html",
                                        reply_markup=ReplyKeyboardRemove())

        # Отправляем сообщение игроку 1 и сохраняем message_id
        msg1 = await callback.bot.send_message(
            player1,
            YOUR_BOARD_TEXT.format(board=print_board(games[game_id]["boards"][player1])),
            parse_mode="html",
            reply_markup=playing_menu(game_id, player2)
        )

        # Отправляем сообщение игроку 2 и сохраняем message_id
        msg2 = await callback.bot.send_message(
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


async def refresh_games_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает callback-запрос обновления списка игр.

    :param callback: Объект callback-запроса от пользователя.
    """
    try:
        await callback.answer()
        await callback.message.edit_text(CHOOSE_CONNECTING_GAME, reply_markup=current_game_menu())
    except Exception:
        pass


def register_handler(dp: Dispatcher) -> None:
    """
    Регистрирует хендлеры команд:
    - Создание новой игры
    - Присоединение к игре
    - Обработка ID игры
    - Callback-обработчики для inline-кнопок
    """
    # Callback-обработчики для inline-кнопок
    dp.callback_query.register(create_game_callback, lambda c: c.data == "new_game")
    dp.callback_query.register(join_game_callback, lambda c: c.data == "join_game")
    dp.callback_query.register(refresh_games_callback, lambda c: c.data == "refresh_games")
    dp.callback_query.register(join_game_by_id_callback, lambda c: c.data and c.data.startswith("join_game_"))
