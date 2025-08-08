from aiogram.types import Message
from typing import Optional

from app.state.in_memory import games
from app.game_logic import print_board, process_shot, check_victory
from app.db_utils.match import update_match_result
from app.db_utils.stats import update_stats_after_match
from app.dependencies import db_session
from app.keyboards import main_menu, enemy_board_keyboard
from app.logger import setup_logger

from app.messages.texts import (
    YOUR_BOARD_TEXT_AFTER_SHOT
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
    username = message.from_user.username

    # Найдем игру, в которой играет user_id
    game_id: Optional[str] = None
    for gid, g in games.items():
        if user_id == g.get("player1") or user_id == g.get("player2"):
            game_id = gid
            break

    if not game_id or game_id not in games:
        await message.answer("❗ Игра не найдена.")
        return

    game = games[game_id]
    player1 = game["player1"]
    player2 = game["player2"]
    opponent_id = player2 if user_id == player1 else player1

    logger.info(f'🏳️ Игрок @{username} сдался, ID игры: {game_id}')

    with db_session() as db:
        update_match_result(db, game_id, winner_id=opponent_id, result="surrender")
        update_stats_after_match(db, winner_id=opponent_id, loser_id=user_id)

    # Удаляем игру и все связи
    games.pop(game_id, None)

    await message.bot.send_message(user_id, "🏳️ Поражение! Вы сдались в игре!", reply_markup=main_menu())
    await message.bot.send_message(opponent_id, "🎉 Победа! Противник сдался!", reply_markup=main_menu())


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
    username = message.from_user.username

    # Найдем игру, в которой играет user_id
    game_id: Optional[str] = None
    for gid, g in games.items():
        if user_id == g.get("player1") or user_id == g.get("player2"):
            game_id = gid
            break

    if not game_id or game_id not in games:
        await message.answer("❗ Игра не найдена.")
        return

    game = games[game_id]

    if user_id != game["turn"]:
        await message.answer("❗ Сейчас не ваш ход.")
        return

    try:
        coord = message.text.upper()
        x = ord(coord[0]) - ord('A')
        y = int(coord[1:]) - 1
        if not (0 <= x < 10 and 0 <= y < 10):
            raise ValueError
    except Exception:
        await message.answer("❗ Неверные координаты. Используйте формат A1.")
        return

    opponent_id = game["player1"] if game["turn"] == game["player2"] else game["player2"]
    board = game["boards"][opponent_id]
    hit = process_shot(board, x, y)

    if check_victory(board):
        with db_session() as db:
            update_match_result(db, game_id, winner_id=user_id, result="normal")
            update_stats_after_match(db, winner_id=user_id, loser_id=opponent_id)

        games.pop(game_id, None)

        await message.answer("🎉 Победа! Вы уничтожили все корабли противника!", reply_markup=main_menu())
        await message.bot.send_message(
            opponent_id,
            f"💥 Поражение! Все ваши корабли уничтожены.\nПобедил @{username}!",
            reply_markup=main_menu()
        )
        return

    if hit:
        # Отправляем новое сообщение стрелявшему
        msg1 = await message.bot.send_message(
            chat_id=user_id,
            text="💥 <b>Попадание!</b> Стреляйте ещё!",
            parse_mode="html",
            reply_markup=enemy_board_keyboard(game_id, opponent_id)
        )

        # Удаляем сообщение соперника
        await message.bot.delete_message(
            chat_id=opponent_id,
            message_id=game.get("message_ids", {}).get(opponent_id, 0)
        )
        # Отправляем новое сообщение сопернику
        msg2 = await message.bot.send_message(
            chat_id=opponent_id,
            text="🔥 <b>По вам попали!</b>\n" + YOUR_BOARD_TEXT_AFTER_SHOT.format(
                board=print_board(board)) + "\n⏳ <b>Ожидайте ход соперника!</b>",
            parse_mode="html",
            reply_markup=enemy_board_keyboard(game_id, user_id)
        )

    else:
        # Меняем ход
        game["turn"] = opponent_id

        # Отправляем новое сообщение стрелявшему
        msg1 = await message.bot.send_message(
            chat_id=user_id,
            text="❌ <b>Мимо!</b> Теперь ходит другой игрок",
            parse_mode="html",
            reply_markup=enemy_board_keyboard(game_id, opponent_id)
        )

        # Удаляем сообщение соперника
        await message.bot.delete_message(
            chat_id=opponent_id,
            message_id=game.get("message_ids", {}).get(opponent_id, 0)
        )
        # Отправляем новое сообщение сопернику
        msg2 = await message.bot.send_message(
            chat_id=opponent_id,
            text=YOUR_BOARD_TEXT_AFTER_SHOT.format(board=print_board(board)) + "\n🎯 <b>Ваш ход!</b>",
            parse_mode="html",
            reply_markup=enemy_board_keyboard(game_id, user_id)
        )

    # Обновляем message_ids в игре
    game.setdefault("message_ids", {})
    game["message_ids"][user_id] = msg1.message_id
    game["message_ids"][opponent_id] = msg2.message_id
