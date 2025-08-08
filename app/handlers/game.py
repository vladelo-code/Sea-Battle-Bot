from aiogram import Dispatcher
from aiogram.types import Message

from app.constants import COORDINATES
from app.services.game_service import handle_surrender, handle_shot


async def shot_command_coord(message: Message) -> None:
    """
    Обрабатывает действия игрока во время игры.

    Если сообщение содержит текст "🏳️ Сдаться" — выполняется логика капитуляции.
    В противном случае — попытка выстрела по координатам.

    :param message: Объект сообщения от пользователя.
    """
    if message.text == "🏳️ Сдаться":
        await handle_surrender(message)
    else:
        await handle_shot(message)


def register_handler(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики сообщений для координатных выстрелов и команды "Сдаться".

    :param dp: Диспетчер бота.
    """
    dp.message.register(shot_command_coord, lambda message: message.text == "🏳️ Сдаться")
    dp.message.register(shot_command_coord, lambda message: message.text in COORDINATES)
