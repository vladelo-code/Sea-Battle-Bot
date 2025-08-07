from aiogram import Dispatcher, types
from aiogram.filters import Command

from app.keyboards import main_menu
from app.logger import setup_logger
from app.services.player_service import register_or_update_player
from app.dependencies import db_session
from app.messages.texts import START_MESSAGE
from app.messages.logs import PLAYER_STARTED_BOT

# Инициализация логгера
logger = setup_logger(__name__)


# Функция для обработки команды /start или '🏠 Главное меню'
async def start_command(message: types.Message):
    logger.info(PLAYER_STARTED_BOT.format(username=message.from_user.username))

    # Регистрируем или обновляем игрока
    with db_session() as db:
        register_or_update_player(db, telegram_id=str(message.from_user.id), username=message.from_user.username)

    await message.answer(START_MESSAGE, reply_markup=main_menu(), parse_mode="HTML", disable_web_page_preview=True)


def register_handler(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
    dp.message.register(start_command, lambda message: message.text == "🏠 Главное меню")
