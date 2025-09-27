import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен бота из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Получаем путь в БД
DATABASE_URL = os.getenv("DATABASE_URL")

# Получаем ID администратора для рассылок
ADMIN_ID = os.getenv("ADMIN_ID")