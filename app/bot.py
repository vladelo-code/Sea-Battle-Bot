import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import register_handlers

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрация обработчиков
register_handlers(dp)


async def main():
    print('✅ Sea-Battle-Bot запущен!')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
