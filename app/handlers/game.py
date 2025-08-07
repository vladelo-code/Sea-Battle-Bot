from aiogram import Dispatcher, types
from aiogram.types import Message
from app.constants import COORDINATES
from app.services.game_service import handle_surrender, handle_shot


def register_handler(dp: Dispatcher):
    dp.message.register(shot_command_coord, lambda message: message.text == "🏳️ Сдаться")
    dp.message.register(shot_command_coord, lambda message: message.text in COORDINATES)


# Основная точка входа
async def shot_command_coord(message: Message):
    if message.text == "🏳️ Сдаться":
        await handle_surrender(message)
    else:
        await handle_shot(message)
