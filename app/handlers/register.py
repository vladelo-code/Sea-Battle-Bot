from aiogram import Dispatcher

from app.handlers import base, stats, game, matchmaking


def register_handlers(dp: Dispatcher):
    base.register_handler(dp)
    stats.register_handler(dp)
    game.register_handler(dp)
    matchmaking.register_handler(dp)
