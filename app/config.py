import os
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен бота из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Получаем путь в БД
DATABASE_URL = os.getenv("DATABASE_URL")

# Получаем ID администратора для рассылок
ADMIN_ID = os.getenv("ADMIN_ID")

# Задаем временную зону по МСК
MOSCOW_TZ = ZoneInfo("Europe/Moscow")

# Список ачивок для соответствующего раздела
ACHIEVEMENT_DEFINITIONS = [
    {
        "code": "full_captain_course",
        "title": "🏁 Полный курс капитана",
        "description": "Сыграй хотя бы 1 матч с ботом на каждом уровне сложности",
    },
    {
        "code": "fleet_marathon",
        "title": "🌀 Марафонец флота",
        "description": "Сыграй суммарно 50 матчей с ботом",
    },
    {
        "code": "speedrunner",
        "title": "🚀 Скорострел",
        "description": "Выиграй матч в мультиплеере за 1 минуту или меньше",
    },
    {
        "code": "night_hunter",
        "title": "🌙 Ночной призрак",
        "description": "Сыграй матч с другом между 0:00 и 3:00 по МСК",
    },
    {
        "code": "morning_sailor",
        "title": "🌞 Утренний моряк",
        "description": "Сыграй матч с другом между 5:00 и 8:00 по МСК",
    },
    {
        "code": "win_streak_10",
        "title": "🔥 Серийный победитель",
        "description": "Выиграй 10 матчей в мультиплеере подряд",
    },
    {
        "code": "easy_breeze",
        "title": "💤 Лёгкий бриз",
        "description": "Выиграй 20 матчей на уровне «easy» против бота",
    },
    {
        "code": "medium_master",
        "title": "🌊 Хозяин прилива",
        "description": "Выиграй 10 матчей на уровне «medium» против бота",
    },
    {
        "code": "hard_master",
        "title": "⚡ Повелитель шторма",
        "description": "Выиграй 5 матчей на уровне «hard» против бота",
    },
    {
        "code": "super_hard_master",
        "title": "👹 Повелитель бездны",
        "description": "Выиграй 3 матча на уровне «super-hard» против бота",
    },
    {
        "code": "brave_loser",
        "title": "🏆 Отважный проигравший",
        "description": "Проиграй (но не сдайся!) 5 раз подряд в мультиплеерном режиме",
    },
    {
        "code": "week_streak",
        "title": "📅 Постоянный моряк",
        "description": "Играй хотя бы 1 матч в мультиплеере каждый день в течение недели",
    },
    {
        "code": "fan_dev",
        "title": "🤩 Фанат",
        "description": "Сыграй хотя бы 1 матч с разработчиком – @vladelo",
    },
    {
        "code": "project_supporter",
        "title": "⚓ Покровитель флота",
        "description": "Поддержи проект донатом в 50 звёзд и получи премиум функции!",
    },
]
