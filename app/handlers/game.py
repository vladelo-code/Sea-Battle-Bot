from aiogram import Dispatcher, types
from aiogram.filters import Command

from app.storage import create_game, join_game, get_game, get_board, switch_turn, get_turn, delete_game
from app.game_logic import print_board, process_shot, check_victory
from app.keyboards import main_menu, connect_menu, playing_menu, current_game_menu, rating_menu
from app.logger import setup_logger

from app.db_utils.match import create_match, update_match_result
from app.db_utils.stats import update_stats_after_match, get_stats, get_top_players
from app.db_utils.player import get_or_create_player, get_player_by_telegram_id
from app.dependencies import get_db

# Инициализация логгера
logger = setup_logger(__name__)

# Создаём глобальный словарь для хранения ID игры
user_game_requests = {}

# Список с координатами
coordinates = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10',
               'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10',
               'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10',
               'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10',
               'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10',
               'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10',
               'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10',
               'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10',
               'I1', 'I2', 'I3', 'I4', 'I5', 'I6', 'I7', 'I8', 'I9', 'I10',
               'J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9', 'J10']

# Создаём глобальный словарь для хранения ID игроков и матчей, в которых они участвуют
current_games = {}


# Функция для хода (выстрела) по координатам с кнопок
async def shot_command_coord(message: types.Message):
    game_id = str(current_games[message.from_user.id])
    game = get_game(game_id)

    if message.text == "🏳️ Сдаться":
        logger.info(f'🏳️ Игрок @{message.from_user.username} сдался, ID игры: {game_id}')
        opponent_id = game["player1"] if game["turn"] == game["player2"] else game["player2"]

        # Обновляем результат матча в БД: победитель — противник, результат — surrender
        db_gen = get_db()
        db = next(db_gen)
        try:
            update_match_result(db, game_id, winner_id=opponent_id, result="surrender")
            update_stats_after_match(db, winner_id=opponent_id, loser_id=message.from_user.id)
        finally:
            db_gen.close()

        del current_games[message.from_user.id]
        del current_games[opponent_id]

        delete_game(game_id)

        await message.answer(f"🏳️ Поражение! Вы сдались в игре!", reply_markup=main_menu())
        await message.bot.send_message(opponent_id, f"🎉 Победа! Противник сдался!", reply_markup=main_menu())
    else:
        coord = message.text.upper()
        x = ord(coord[0]) - ord('A')
        y = int(coord[1:]) - 1

        if game and message.from_user.id == get_turn(game_id):
            opponent_id = game["player1"] if game["turn"] == game["player2"] else game["player2"]
            board = get_board(game_id, opponent_id)

            if 0 <= x < 10 and 0 <= y < 10:
                hit = process_shot(board, x, y)

                # Проверка на победу после выстрела
                if check_victory(board):
                    # Обновляем результат матча в БД: победитель — current user, результат — normal
                    db_gen = get_db()
                    db = next(db_gen)
                    try:
                        update_match_result(db, game_id, winner_id=message.from_user.id, result="normal")
                        update_stats_after_match(db, winner_id=message.from_user.id, loser_id=opponent_id)
                    finally:
                        db_gen.close()

                    del current_games[message.from_user.id]
                    del current_games[opponent_id]
                    winner = message.from_user.username
                    loser = await message.bot.get_chat(opponent_id)
                    await message.answer(f"🎉 Победа! Вы уничтожили все корабли противника!", reply_markup=main_menu())
                    await message.bot.send_message(opponent_id,
                                                   f"💥 Поражение! Все ваши корабли уничтожены.\nПобедил @{winner}!",
                                                   reply_markup=main_menu())
                    delete_game(game_id)
                    return

                switch_turn(game_id)

                result = "💥 Попадание!" if hit else "❌ Мимо!"
                board_view = print_board(board, hide_ships=True)
                await message.answer(
                    f"{result}\nОбновлённое поле противника:\n{board_view}\n Ожидайте ход другого игрока!",
                    parse_mode="html", reply_markup=types.ReplyKeyboardRemove())
                await message.bot.send_message(
                    opponent_id,
                    f"Ход противника завершён.\n"
                    f"Обновлённое поле после выстрела:\n{board_view}\n Ваш ход!", parse_mode="html",
                    reply_markup=playing_menu(game_id, message.from_user.id))
            else:
                await message.answer("❗ Неверные координаты. Используйте формат A1.")
        else:
            await message.answer("❗ Сейчас не ваш ход или игра не найдена.")


def register_handler(dp: Dispatcher):
    # Вызываем функцию хода (выстрела) по фразе введенным координатам или сдаемся
    dp.message.register(shot_command_coord, lambda message: message.text == "🏳️ Сдаться")
    dp.message.register(shot_command_coord, lambda message: message.text in coordinates)
