import asyncio
from aiogram import Bot, Dispatcher

from app.handlers.register import register_handlers
from app.logger import setup_logger
from app.config import BOT_TOKEN

# Инициализация логгера
logger = setup_logger("bot")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрация обработчиков
register_handlers(dp)


async def main():
    logger.info("✅ Морской Бой Бот запущен!")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"Ошибка в bot.py: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
