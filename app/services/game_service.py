from aiogram.types import Message, ReplyKeyboardRemove
from typing import Optional

from app.state.in_memory import games
from app.game_logic import print_board, process_shot, check_victory
from app.db_utils.match import update_match_result
from app.db_utils.stats import update_stats_after_match
from app.dependencies import db_session
from app.keyboards import after_game_menu, enemy_board_keyboard
from app.logger import setup_logger
from app.services.achievements_service import evaluate_achievements_after_multiplayer_match

from app.messages.texts import (
    GAME_NOT_FOUND, LOSER_SUR, WINNER_SUR, AD_AFTER_GAME, NOT_YOUR_TURN, BAD_COORDINATES, WINNER, LOSER,
    SUCCESSFUL_SHOT, YOUR_BOARD_TEXT_AFTER_SUCCESS_SHOT, BAD_SHOT, YOUR_BOARD_TEXT_AFTER_BAD_SHOT
)

logger = setup_logger(__name__)


async def handle_surrender(message: Message) -> None:
    """
    Обрабатывает сдачу игрока в игре:
    - Находит игру по ID пользователя
    - Обновляет результат матча в базе
    - Обновляет статистику игроков
    - Удаляет игру из памяти
    - Отправляет сообщения о поражении и победе игрокам

    :param message: Объект сообщения от игрока, сдающегося.
    """
    user_id = message.from_user.id

    # Найдем игру, в которой играет user_id
    game_id: Optional[str] = None
    for gid, g in games.items():
        if user_id == g.get("player1") or user_id == g.get("player2"):
            game_id = gid
            break

    if not game_id or game_id not in games:
        await message.answer(GAME_NOT_FOUND.format(game_id=game_id))
        return

    game = games[game_id]
    player1 = game["player1"]
    player2 = game["player2"]
    opponent_id = player2 if user_id == player1 else player1

    usernames = game.get("usernames", {})
    loser_username = usernames.get(user_id, "Игрок 1")
    winner_username = usernames.get(opponent_id, "Игрок 2")

    logger.info(f'🏳️ Игрок @{loser_username} сдался, ID игры: {game_id}')
    logger.info(f'🎉️ Игрок @{winner_username} выиграл, ID игры: {game_id}')

    with db_session() as db:
        match = update_match_result(db, game_id, winner_id=opponent_id, result="surrender")
        update_stats_after_match(db, winner_id=opponent_id, loser_id=user_id)
        try:
            if match:
                evaluate_achievements_after_multiplayer_match(db, match)
        except Exception:
            pass

    winner_board = game["boards"].get(opponent_id)
    loser_board = game["boards"].get(user_id)

    # Удаляем игру и все связи
    games.pop(game_id, None)

    await message.bot.send_message(
        user_id,
        LOSER_SUR.format(board=print_board(winner_board), username=winner_username),
        parse_mode="html",
        reply_markup=ReplyKeyboardRemove()
    )

    await message.bot.send_message(
        user_id,
        text=AD_AFTER_GAME,
        parse_mode="html",
        disable_web_page_preview=True,
        reply_markup=after_game_menu()
    )

    await message.bot.send_message(
        opponent_id,
        WINNER_SUR.format(board=print_board(loser_board), username=loser_username),
        parse_mode="html",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.bot.send_message(
        opponent_id,
        text=AD_AFTER_GAME,
        parse_mode="html",
        disable_web_page_preview=True,
        reply_markup=after_game_menu()
    )


async def handle_shot(message: Message) -> None:
    """
    Обрабатывает выстрел игрока по координатам:
    - Находит игру по ID пользователя
    - Проверяет, является ли ход игрока текущим
    - Парсит координаты выстрела
    - Обновляет состояние доски и игры
    - Проверяет победу
    - Отправляет обновления игрокам
    - Обновляет ID сообщений для последующего удаления/редактирования

    :param message: Объект сообщения с координатами выстрела.
    """
    user_id = message.from_user.id
    # username = message.from_user.username

    # Найдем игру, в которой играет user_id
    game_id: Optional[str] = None
    for gid, g in games.items():
        if user_id == g.get("player1") or user_id == g.get("player2"):
            game_id = gid
            break

    if not game_id or game_id not in games:
        await message.answer(GAME_NOT_FOUND.format(game_id=game_id))
        return

    game = games[game_id]

    if user_id != game["turn"]:
        await message.answer(NOT_YOUR_TURN)
        return

    try:
        coord = message.text.upper()
        x = ord(coord[0]) - ord('A')
        y = int(coord[1:]) - 1
        if not (0 <= x < 10 and 0 <= y < 10):
            raise ValueError
    except Exception:
        await message.answer(BAD_COORDINATES)
        return

    opponent_id = game["player1"] if game["turn"] == game["player2"] else game["player2"]
    board = game["boards"][opponent_id]
    hit = process_shot(board, x, y)

    # Получаем username'ы из словаря, только для сообщений
    usernames = game.get("usernames", {})
    current_username = usernames.get(user_id, "Игрок 1")
    opponent_username = usernames.get(opponent_id, "Игрок 2")

    if check_victory(board):
        with db_session() as db:
            match = update_match_result(db, game_id, winner_id=user_id, result="normal")
            update_stats_after_match(db, winner_id=user_id, loser_id=opponent_id)
            try:
                if match:
                    evaluate_achievements_after_multiplayer_match(db, match)
            except Exception:
                pass

        winner_board = game["boards"].get(user_id)
        loser_board = game["boards"].get(opponent_id)

        games.pop(game_id, None)

        await message.bot.send_message(
            opponent_id,
            LOSER.format(board=print_board(winner_board), username=current_username),
            parse_mode="html",
            reply_markup=ReplyKeyboardRemove()
        )

        await message.bot.send_message(
            opponent_id,
            text=AD_AFTER_GAME,
            parse_mode="html",
            disable_web_page_preview=True,
            reply_markup=after_game_menu()
        )

        await message.bot.send_message(
            user_id,
            WINNER.format(board=print_board(loser_board), username=opponent_username),
            parse_mode="html",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.bot.send_message(
            user_id,
            text=AD_AFTER_GAME,
            parse_mode="html",
            disable_web_page_preview=True,
            reply_markup=after_game_menu()
        )

        return

    if hit:
        # Отправляем новое сообщение стрелявшему
        msg1 = await message.bot.send_message(
            chat_id=user_id,
            text=SUCCESSFUL_SHOT,
            parse_mode="html",
            reply_markup=enemy_board_keyboard(game_id, opponent_id)
        )

        # Отправляем новое сообщение сопернику
        msg2 = await message.bot.send_message(
            chat_id=opponent_id,
            text=YOUR_BOARD_TEXT_AFTER_SUCCESS_SHOT.format(board=print_board(board)),
            parse_mode="html",
            reply_markup=enemy_board_keyboard(game_id, user_id)
        )

        # # Удаляем сообщение соперника
        # await message.bot.delete_message(
        #     chat_id=opponent_id,
        #     message_id=game.get("message_ids", {}).get(opponent_id, 0)
        # )

    else:
        # Меняем ход
        game["turn"] = opponent_id

        # Отправляем новое сообщение стрелявшему
        msg1 = await message.bot.send_message(
            chat_id=user_id,
            text=BAD_SHOT,
            parse_mode="html",
            reply_markup=enemy_board_keyboard(game_id, opponent_id)
        )

        # Отправляем новое сообщение сопернику
        msg2 = await message.bot.send_message(
            chat_id=opponent_id,
            text=YOUR_BOARD_TEXT_AFTER_BAD_SHOT.format(board=print_board(board)),
            parse_mode="html",
            reply_markup=enemy_board_keyboard(game_id, user_id)
        )

        # # Удаляем сообщение соперника
        # await message.bot.delete_message(
        #     chat_id=opponent_id,
        #     message_id=game.get("message_ids", {}).get(opponent_id, 0)
        # )

    # Обновляем message_ids в игре
    game.setdefault("message_ids", {})
    game["message_ids"][user_id] = msg1.message_id
    game["message_ids"][opponent_id] = msg2.message_id
