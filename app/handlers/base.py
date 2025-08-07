from aiogram import Dispatcher, types
from aiogram.filters import Command

from app.keyboards import main_menu
from app.logger import setup_logger
from app.db_utils.player import get_or_create_player
from app.dependencies import get_db
from app.messages.texts import START_MESSAGE

# Инициализация логгера
logger = setup_logger(__name__)


# Функция для обработки команды /start
async def start_command(message: types.Message):
    logger.info(f'👋 Игрок @{message.from_user.username} запустил бота!')

    # Регистрируем или обновляем игрока
    db_gen = get_db()
    db = next(db_gen)
    try:
        get_or_create_player(db, telegram_id=str(message.from_user.id), username=message.from_user.username)
    finally:
        db_gen.close()

    await message.answer(START_MESSAGE, reply_markup=main_menu(), parse_mode="HTML", disable_web_page_preview=True)


def register_handler(dp: Dispatcher):
    # Вызываем функцию приветствия по команде /start или '🏠 Главное меню'
    dp.message.register(start_command, Command("start"))
    dp.message.register(start_command, lambda message: message.text == "🏠 Главное меню")
