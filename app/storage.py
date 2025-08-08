from app.game_logic import create_empty_board, place_all_ships
from app.utils import generate_game_id

# Тут хранятся текущие игры с расширенной структурой
games = {}

# Создаём глобальный словарь для хранения ID игры, где пользователь ожидает действия
user_game_requests = {}


# Функция для создания игры
def create_game(player_id: int, username: str):
    game_id = generate_game_id()
    board = create_empty_board()
    place_all_ships(board)
    games[game_id] = {
        "player1": player_id,
        "player2": None,
        "boards": {player_id: board},
        "turn": player_id,
        "usernames": {player_id: username},
        "message_ids": {},
    }
    return game_id


# Функция для присоединения к игре
def join_game(game_id: str, player_id: int, username: str):
    game = games.get(game_id)
    if game and game["player2"] is None:
        board = create_empty_board()
        place_all_ships(board)
        game["player2"] = player_id
        game["boards"][player_id] = board
        game["usernames"][player_id] = username
        return True
    return False


# Функция для получения игры
def get_game(game_id: str):
    return games.get(game_id)


# Функция смены хода
def switch_turn(game_id: str):
    game = games[game_id]
    game["turn"] = game["player1"] if game["turn"] == game["player2"] else game["player2"]


# Функция получения игрового поля
def get_board(game_id: str, player_id: int):
    return games[game_id]["boards"][player_id]


# Функция получения текущего хода
def get_turn(game_id: str):
    return games[game_id]["turn"]


# Функция удаления игры
def delete_game(game_id: str):
    if game_id in games:
        del games[game_id]
