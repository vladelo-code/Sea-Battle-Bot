from aiogram import Dispatcher

from app.handlers import base, stats, game, matchmaking, records, broadcast, bot_game, bot_analytics, achievements, donation


def register_handlers(dp: Dispatcher) -> None:
    """
    Регистрирует все обработчики команд и сообщений для бота.

    :param dp: Экземпляр Dispatcher из aiogram.
    """
    base.register_handler(dp)
    stats.register_handler(dp)
    game.register_handler(dp)
    matchmaking.register_handler(dp)
    records.register_handler(dp)
    broadcast.register_handler(dp)
    bot_game.register_handler(dp)
    bot_analytics.register_handler(dp)
    achievements.register_handler(dp)
    donation.register_handler(dp)
