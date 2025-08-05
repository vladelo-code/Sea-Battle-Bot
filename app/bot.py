import asyncio
from aiogram import Bot, Dispatcher

from app.handlers import register_handlers
from app.logger import setup_logger

from config import BOT_TOKEN

# Инициализация логгера
logger = setup_logger("bot")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрация обработчиков
register_handlers(dp)


async def main():
    logger.info("✅ Sea-Battle-Bot запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
