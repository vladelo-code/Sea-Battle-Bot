from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

from app.keyboards import main_menu
from app.logger import setup_logger
from app.services.player_service import register_or_update_player
from app.dependencies import db_session
from app.messages.texts import START_MESSAGE

# Инициализация логгера
logger = setup_logger(__name__)


async def start_command(message: Message) -> None:
    """
    Обрабатывает команду /start или кнопку '🏠 Главное меню'.
    - Регистрирует или обновляет информацию об игроке.
    - Отправляет приветственное сообщение с клавиатурой главного меню.

    :param message: Объект входящего сообщения от пользователя.
    """
    logger.info(f"👋 Игрок @{message.from_user.username} запустил бота!")

    with db_session() as db:
        register_or_update_player(db, telegram_id=str(message.from_user.id), username=message.from_user.username)

    await message.answer(START_MESSAGE, reply_markup=main_menu(), parse_mode="HTML", disable_web_page_preview=True)


def register_handler(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики команд:
    - /start
    - '🏠 Главное меню'

    :param dp: Объект диспетчера aiogram.
    """
    dp.message.register(start_command, Command("start"))
    dp.message.register(start_command, lambda message: message.text == "🏠 Главное меню")
