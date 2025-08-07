from aiogram.types import Message, ReplyKeyboardRemove

from app.storage import get_game, get_board, switch_turn, get_turn, delete_game, current_games
from app.game_logic import print_board, process_shot, check_victory
from app.db_utils.match import update_match_result
from app.db_utils.stats import update_stats_after_match
from app.dependencies import get_db
from app.keyboards import main_menu, playing_menu
from app.logger import setup_logger

logger = setup_logger(__name__)


async def handle_surrender(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    game_id = str(current_games.get(user_id))

    if not game_id or not get_game(game_id):
        await message.answer("❗ Игра не найдена.")
        return

    game = get_game(game_id)
    opponent_id = game["player1"] if game["turn"] == game["player2"] else game["player2"]

    logger.info(f'🏳️ Игрок @{username} сдался, ID игры: {game_id}')

    db_gen = get_db()
    db = next(db_gen)
    try:
        update_match_result(db, game_id, winner_id=opponent_id, result="surrender")
        update_stats_after_match(db, winner_id=opponent_id, loser_id=user_id)
    finally:
        db_gen.close()

    current_games.pop(user_id, None)
    current_games.pop(opponent_id, None)
    delete_game(game_id)

    await message.answer("🏳️ Поражение! Вы сдались в игре!", reply_markup=main_menu())
    await message.bot.send_message(opponent_id, "🎉 Победа! Противник сдался!", reply_markup=main_menu())


async def handle_shot(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    game_id = str(current_games.get(user_id))

    if not game_id or not get_game(game_id):
        await message.answer("❗ Игра не найдена.")
        return

    game = get_game(game_id)

    if user_id != get_turn(game_id):
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
    board = get_board(game_id, opponent_id)
    hit = process_shot(board, x, y)

    if check_victory(board):
        db_gen = get_db()
        db = next(db_gen)
        try:
            update_match_result(db, game_id, winner_id=user_id, result="normal")
            update_stats_after_match(db, winner_id=user_id, loser_id=opponent_id)
        finally:
            db_gen.close()

        current_games.pop(user_id, None)
        current_games.pop(opponent_id, None)
        delete_game(game_id)

        await message.answer("🎉 Победа! Вы уничтожили все корабли противника!", reply_markup=main_menu())
        await message.bot.send_message(
            opponent_id,
            f"💥 Поражение! Все ваши корабли уничтожены.\nПобедил @{username}!",
            reply_markup=main_menu()
        )
        return

    switch_turn(game_id)

    result = "💥 Попадание!" if hit else "❌ Мимо!"
    board_view = print_board(board, hide_ships=True)

    await message.answer(
        f"{result}\nОбновлённое поле противника:\n{board_view}\nОжидайте ход другого игрока!",
        parse_mode="html",
        reply_markup=ReplyKeyboardRemove()
    )

    await message.bot.send_message(
        opponent_id,
        f"Ход противника завершён.\nОбновлённое поле после выстрела:\n{board_view}\nВаш ход!",
        parse_mode="html",
        reply_markup=playing_menu(game_id, user_id)
    )
