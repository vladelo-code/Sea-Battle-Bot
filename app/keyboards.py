from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from storage import games


# Клавиатура в главном меню
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Новая игра")],
            [KeyboardButton(text="📎 Присоединиться к игре")],
            [KeyboardButton(text="👤 Мой профиль")],
            [KeyboardButton(text="🥇 Рейтинг")]
        ],
        resize_keyboard=True
    )
    return keyboard


# Функция для подключения к игре
def connect_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📎 Присоединиться к игре")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard


# Клавиатура с динамическим полем игры
def playing_menu(game_id, player_id):
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
                     [
                         KeyboardButton(text=(cell if cell in ["❌", "💥"] else f"{chr(65 + row)}{col + 1}"))
                         for col, cell in enumerate(games[game_id]['boards'][player_id][row])
                     ]
                     for row in range(10)
                 ] + [
                     [KeyboardButton(text="🏳️ Сдаться")]
                 ],
    )
    return keyboard


# Клавиатура со списком активных игр
def current_game_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{game}") for game in games],
            [KeyboardButton(text="🚀 Новая игра")],
            [KeyboardButton(text="🔃 Обновить список игр")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard


# Клавиатура в меню с рейтингом
def rating_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ℹ️ О рейтинге")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard
