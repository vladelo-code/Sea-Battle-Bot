import asyncio

from app.state.in_memory import user_game_requests, games
from app.logger import setup_logger

logger = setup_logger(__name__)


async def remove_game_if_no_join(game_id: str, bot, delay: int = 300) -> None:
    """
    Удаляет игру через delay секунд, если второй игрок так и не присоединился.

    :param game_id: ID игры.
    :param bot: Объект бота для удаления сообщений.
    :param delay: Время ожидания в секундах перед удалением.
    """
    await asyncio.sleep(delay)
    game = games.get(game_id)
    if game and game["player2"] is None:
        logger.info(f"🧹 Автоудаление игры {game_id} — второй игрок не присоединился.")
        player1_id = game["player1"]

        # Удаляем сообщение о создании игры у первого игрока
        creation_message_id = game.get("creation_message_id")
        if creation_message_id:
            try:
                await bot.delete_message(player1_id, creation_message_id)
            except Exception:
                pass

        user_game_requests.pop(player1_id, None)
        games.pop(game_id, None)
