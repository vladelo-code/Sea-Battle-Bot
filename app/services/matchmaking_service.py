from app.state.in_memory import user_game_requests, games
from app.storage import create_game, join_game
from app.db_utils.match import create_match
from app.db_utils.player import get_or_create_player
from app.dependencies import db_session
from app.logger import setup_logger

logger = setup_logger(__name__)


def try_create_game(user_id: int, username: str) -> str:
    """
    Создает новую игру и отмечает пользователя, что он создал игру и ожидает присоединения второго игрока.

    :param user_id: ID пользователя, создающего игру.
    :param username: Username пользователя.
    :return: ID созданной игры.
    """
    game_id = create_game(user_id, username)
    user_game_requests[user_id] = None  # пометка, что игрок создал игру и ждёт присоединения
    return game_id


def try_join_game(game_id: str, user_id: int, username: str) -> str | dict:
    """
    Пытается присоединить пользователя к существующей игре.

    :param game_id: ID игры, к которой присоединяется игрок.
    :param user_id: ID присоединяющегося игрока.
    :param username: Username присоединяющегося игрока.
    :return: Строка с ошибкой ('not_found', 'same_game', 'invalid') или словарь с данными об успешном присоединении.
    """
    if user_id in user_game_requests and user_game_requests[user_id] is None:
        game = games.get(game_id)
        if not game:
            return "not_found"

        # Проверяем, не пытается ли игрок присоединиться к своей же игре
        if user_id == game["player1"]:
            return "same_game"

        # Если игрок уже в другой игре — удаляем ту игру
        for gid, g in list(games.items()):
            if user_id == g.get("player1") or user_id == g.get("player2"):
                # Удаляем игру, в которой игрок участвует
                games.pop(gid, None)
                break

        # Присоединяем второго игрока
        if not join_game(game_id, user_id, username):
            return "not_found"

        # Работа с БД
        with db_session() as db:
            get_or_create_player(db, telegram_id=str(game["player1"]))
            get_or_create_player(db, telegram_id=str(user_id), username=username)
            create_match(db, game_id, game["player1"], user_id)

        # Сохраняем username второго игрока
        game = games[game_id]
        game["player2"] = user_id
        game["usernames"] = game.get("usernames", {})
        game["usernames"][user_id] = username

        # Обновляем статус в user_game_requests (удаляем)
        user_game_requests.pop(user_id, None)

        return {
            "status": "joined",
            "player1": game["player1"],
            "player2": user_id,
            "game_id": game_id,
        }

    return "invalid"
