from aiogram import Dispatcher
from aiogram.types import Message

from app.state.constants import COORDINATES
from app.services.game_service import handle_surrender, handle_shot
from app.services.bot_game_service import handle_player_shot_vs_bot, handle_surrender_vs_bot
from app.state.in_memory import games


async def shot_command_coord(message: Message) -> None:
    """
    Обрабатывает действия игрока во время игры.

    Если сообщение содержит текст "🏳️ Сдаться" — выполняется логика капитуляции.
    В противном случае — попытка выстрела по координатам.

    :param message: Объект сообщения от пользователя.
    """
    # Определяем тип игры до обработки
    user_id = message.from_user.id
    chosen_game = None
    # 1) Приоритет — игра, где сейчас ход пользователя
    for gid, g in games.items():
        if (user_id == g.get("player1") or user_id == g.get("player2")) and g.get("turn") == user_id:
            # Пропускаем незаполненные PvP игры
            if not g.get("is_bot_game") and not (g.get("player1") and g.get("player2")):
                continue
            chosen_game = g
            break
    # 2) Если нет — игра с ботом
    if not chosen_game:
        for gid, g in games.items():
            if (user_id == g.get("player1") or user_id == g.get("player2")) and g.get("is_bot_game"):
                chosen_game = g
                break
    # 3) Если нет — любая активная PvP-игра (оба игрока на месте)
    if not chosen_game:
        for gid, g in games.items():
            if (user_id == g.get("player1") or user_id == g.get("player2")) and g.get("player1") and g.get("player2"):
                chosen_game = g
                break
    is_bot_game = bool(chosen_game and chosen_game.get("is_bot_game"))

    if message.text == "🏳️ Сдаться":
        if is_bot_game:
            await handle_surrender_vs_bot(message)
        else:
            await handle_surrender(message)
    else:
        if is_bot_game:
            await handle_player_shot_vs_bot(message)
        else:
            await handle_shot(message)


def register_handler(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики сообщений для координатных выстрелов и команды "Сдаться".

    :param dp: Диспетчер бота.
    """
    dp.message.register(shot_command_coord, lambda message: message.text == "🏳️ Сдаться")
    dp.message.register(shot_command_coord, lambda message: message.text in COORDINATES)
