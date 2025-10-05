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
        "title": "⚡ Скорострел",
        "description": "Выиграй матч в мультиплеере за 1 минуту или меньше",
    },
    {
        "code": "night_hunter",
        "title": "🌙 Ночной охотник",
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
        "title": "😴 Легкий ветер",
        "description": "Выиграй 20 матчей на «easy» уровне с ботом",
    },
    {
        "code": "medium_master",
        "title": "🌊 Средний мастер морей",
        "description": "Выиграй 10 матчей на «medium» уровне с ботом",
    },
    {
        "code": "hard_master",
        "title": "🔱 Мастер сложности",
        "description": "Выиграй 5 матчей на «hard» уровне с ботом",
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
]
