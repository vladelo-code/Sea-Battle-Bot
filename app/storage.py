from typing import Optional

from app.game_logic import create_empty_board, place_all_ships
from app.utils import generate_game_id
from app.utils.none_username import safe_username
from app.state.in_memory import games
from app.messages.texts import UNKNOWN_USERNAME_FIRST, UNKNOWN_USERNAME_SECOND



def create_game(player_id: int, username: str) -> str:
    """
    Создает новую игру с игроком player_id и его username.
    Генерирует уникальный ID игры, создает доску, размещает корабли и инициализирует структуру игры.

    :param player_id: ID первого игрока.
    :param username: Username первого игрока.
    :return: Сгенерированный ID игры.
    """
    game_id = generate_game_id()
    board = create_empty_board()
    place_all_ships(board)
    games[game_id] = {
        "player1": player_id,
        "player2": None,
        "boards": {player_id: board},
        "turn": player_id,
        "usernames": {player_id: safe_username(username, UNKNOWN_USERNAME_FIRST)},
        "message_ids": {},
    }
    return game_id


def join_game(game_id: str, player_id: int, username: str) -> bool:
    """
    Присоединяет второго игрока к существующей игре, если место свободно.
    Создает игровое поле для второго игрока и сохраняет его username.

    :param game_id: ID игры для присоединения.
    :param player_id: ID второго игрока.
    :param username: Username второго игрока.
    :return: True если присоединение прошло успешно, иначе False.
    """
    game = games.get(game_id)
    if game and game["player2"] is None:
        board = create_empty_board()
        place_all_ships(board)
        game["player2"] = player_id
        game["boards"][player_id] = board
        game["usernames"][player_id] = safe_username(username, UNKNOWN_USERNAME_SECOND)
        return True
    return False


def create_bot_game(player_id: int, username: str, difficulty: str) -> str:
    """
    Создает игру против бота. Второй игрок — виртуальный bot_id. Сохраняет флаг is_bot_game и сложность.

    :param player_id: ID человеческого игрока
    :param username: username игрока
    :param difficulty: уровень сложности («easy», «medium», «hard»)
    :return: game_id
    """
    from app.services.bot_ai import BotAI  # локальный импорт, чтобы избежать циклов

    game_id = generate_game_id()
    human_board = create_empty_board()
    bot_board = create_empty_board()
    place_all_ships(human_board)
    place_all_ships(bot_board)

    bot_id = -abs(hash((player_id, game_id)))

    games[game_id] = {
        "player1": player_id,
        "player2": bot_id,
        "bot_id": bot_id,
        "is_bot_game": True,
        "difficulty": difficulty,
        "boards": {player_id: human_board, bot_id: bot_board},
        "turn": player_id,
        "usernames": {player_id: safe_username(username, UNKNOWN_USERNAME_FIRST), bot_id: "vladelo_sea_battle_bot"},
        "message_ids": {},
        "bot_state": {"ai": BotAI(difficulty)},
    }
    return game_id


def get_game(game_id: str) -> Optional[dict]:
    """
    Возвращает структуру игры по game_id или None если игры нет.

    :param game_id: ID игры.
    :return: Словарь с данными игры или None.
    """
    return games.get(game_id)


def switch_turn(game_id: str) -> None:
    """
    Меняет текущего игрока, чей ход, на противоположного.

    :param game_id: ID игры.
    """
    game = games[game_id]
    game["turn"] = game["player1"] if game["turn"] == game["player2"] else game["player2"]


def get_board(game_id: str, player_id: int) -> list[list[str]]:
    """
    Возвращает игровое поле указанного игрока в игре.

    :param game_id: ID игры.
    :param player_id: ID игрока.
    :return: Игровое поле игрока.
    """
    return games[game_id]["boards"][player_id]


def get_turn(game_id: str) -> int:
    """
    Возвращает ID игрока, который должен сделать ход.

    :param game_id: ID игры.
    :return: ID игрока, чей ход.
    """
    return games[game_id]["turn"]


def delete_game(game_id: str) -> None:
    """
    Удаляет игру из словаря игр по ID.

    :param game_id: ID игры для удаления.
    """
    if game_id in games:
        del games[game_id]
