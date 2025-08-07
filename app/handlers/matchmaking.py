from aiogram import Dispatcher, types

from app.storage import create_game, join_game, get_game, get_board, switch_turn, get_turn, delete_game
from app.game_logic import print_board, process_shot, check_victory
from app.keyboards import main_menu, connect_menu, playing_menu, current_game_menu, rating_menu
from app.logger import setup_logger

from app.db_utils.match import create_match, update_match_result
from app.db_utils.stats import update_stats_after_match, get_stats, get_top_players
from app.db_utils.player import get_or_create_player, get_player_by_telegram_id
from app.dependencies import get_db
from app.messages.texts import STARTING_GAME, STARTING_GAME_ERROR, CHOOSE_CONNECTING_GAME, JOIN_CONNECTING_GAME_ERROR

from app.handlers.game import user_game_requests, current_games

# Инициализация логгера
logger = setup_logger(__name__)

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


# Функция для создания игры
async def create_game_command(message: types.Message):
    if message.from_user.id not in current_games:
        game_id = create_game(message.from_user.id)
        logger.info(f'🚀 Игрок @{message.from_user.username} создал игру, ID игры: {game_id}')
        current_games[message.from_user.id] = game_id
        await message.answer(STARTING_GAME.format(game_id=game_id), reply_markup=connect_menu())
    else:
        logger.info(f'❗ Игрок @{message.from_user.username} пытался создать ещё игру, не закончив предыдущую.')
        await message.answer(STARTING_GAME_ERROR)


# Функция для подключения к игре
async def process_game_id(message: types.Message):
    user_game_requests[message.from_user.id] = None
    await message.answer(CHOOSE_CONNECTING_GAME, reply_markup=current_game_menu())


# Функция для подключения к игре
async def join_game_command(message: types.Message):
    try:
        game_id = message.text
        user_id = message.from_user.id
        if user_id in current_games and current_games[user_id] == game_id:
            logger.warning(
                f'❗ Пользователь @{message.from_user.username} пытался подключиться к своей же игре с ID: {game_id}')
            await message.answer(JOIN_CONNECTING_GAME_ERROR, reply_markup=current_game_menu())
        else:
            if user_id in user_game_requests and user_game_requests[user_id] is None:
                game = get_game(game_id)
                if game:
                    # Если игрок уже создал свою игру — удаляем её, чтобы он не участвовал в двух
                    if user_id in current_games:
                        old_game_id = current_games[user_id]
                        delete_game(old_game_id)
                        del current_games[user_id]

                    if join_game(game_id, user_id):
                        # Создаем матч в БД при присоединении второго игрока
                        db_gen = get_db()
                        db = next(db_gen)
                        try:
                            # Обновляем или создаем игроков
                            get_or_create_player(db, telegram_id=str(game["player1"]))
                            get_or_create_player(db, telegram_id=str(user_id), username=message.from_user.username)

                            create_match(db, game_id, game["player1"], user_id)
                        finally:
                            db_gen.close()

                        game = get_game(game_id)
                        player1 = game["player1"]
                        player2 = game["player2"]
                        logger.info(f'➕ Игрок @{message.from_user.username} присоединился к игре, ID игры: {game_id}')
                        current_games[message.from_user.id] = game_id
                        await message.answer(f"✅ Вы успешно присоединились к игре с ID: {game_id}!")
                        await message.bot.send_message(player1, f"🎮 Игра началась!\n1️⃣ Вы ходите первым!",
                                                       reply_markup=types.ReplyKeyboardRemove())
                        await message.bot.send_message(player2, f"🎮 Игра началась!\n2️⃣ Вы ходите вторым!",
                                                       reply_markup=types.ReplyKeyboardRemove())
                        await message.bot.send_message(player1,
                                                       "Ваше поле:\n" + print_board(get_board(game_id, player1)),
                                                       parse_mode="html", reply_markup=playing_menu(game_id, player2))
                        await message.bot.send_message(player2,
                                                       "Ваше поле:\n" + print_board(get_board(game_id, player2)),
                                                       parse_mode="html")
                    else:
                        await message.answer(f"❗ Игра с ID: {game_id} не найдена или уже заполнена.")
                else:
                    await message.answer(f"❗ Игра с ID: {game_id} не найдена или уже заполнена.")
                # Убираем пользователя из ожидания
                del user_game_requests[user_id]
    except IndexError:
        await message.answer(f"❗ Вы ввели некорректные данные.")


def register_handler(dp: Dispatcher):
    # Вызываем функцию создания новой игры по фразе '🚀 Новая игра'
    dp.message.register(create_game_command, lambda message: message.text == "🚀 Новая игра")

    # Вызываем функцию подключения к игре по фразе '📎 Присоединиться к игре' или '🔃 Обновить список игр'
    dp.message.register(process_game_id, lambda
        message: message.text == "📎 Присоединиться к игре" or message.text == "🔃 Обновить список игр")
    dp.message.register(join_game_command)
