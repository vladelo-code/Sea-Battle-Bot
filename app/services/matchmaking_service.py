from app.storage import create_game, join_game, get_game, delete_game
from app.db_utils.match import create_match
from app.db_utils.player import get_or_create_player
from app.dependencies import db_session
from app.logger import setup_logger

logger = setup_logger(__name__)


def try_create_game(user_id: int):
    return create_game(user_id)


def try_join_game(game_id: str, user_id: int, username: str, current_games: dict, user_game_requests: dict):
    if user_id in current_games and current_games[user_id] == game_id:
        return "same_game"

    if user_id in user_game_requests and user_game_requests[user_id] is None:
        game = get_game(game_id)
        if not game:
            return "not_found"

        # Удаляем старую игру, если игрок уже в игре
        if user_id in current_games:
            delete_game(current_games[user_id])
            del current_games[user_id]

        if not join_game(game_id, user_id):
            return "not_found"

        # Работа с БД
        with db_session() as db:
            get_or_create_player(db, telegram_id=str(game["player1"]))
            get_or_create_player(db, telegram_id=str(user_id), username=username)
            create_match(db, game_id, game["player1"], user_id)

        return {
            "status": "joined",
            "player1": game["player1"],
            "player2": user_id,
            "game_id": game_id,
        }

    return "invalid"