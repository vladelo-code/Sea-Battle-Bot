from app.db_utils.player import get_or_create_player


def register_or_update_player(db, telegram_id: str, username: str):
    return get_or_create_player(db, telegram_id, username)
