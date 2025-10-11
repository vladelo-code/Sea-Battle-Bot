from typing import Optional
import asyncio

# Тут хранятся текущие игры с расширенной структурой
games: dict[str, dict] = {}

# Создаём глобальный словарь для хранения ID игры, где пользователь ожидает действия
user_game_requests: dict[int, Optional[None]] = {}

# Словарь для хранения активных жалоб и их таймеров
complaint_timers: dict[str, asyncio.Task] = {}
