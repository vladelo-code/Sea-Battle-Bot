from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.storage import games


def main_menu() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру главного меню с основными командами:
    - Новая игра
    - Присоединиться к игре
    - Мой профиль
    - Рейтинг
    """
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


def connect_menu() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для меню подключения к игре:
    - Присоединиться к игре
    - Главное меню
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📎 Присоединиться к игре")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard


def playing_menu(game_id: str, player_id: int) -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру с игровым полем для текущего игрока.
    Отображает клетки с состояниями: попадание, промах или координаты.
    Добавляет кнопку 'Сдаться'.

    :param game_id: ID текущей игры.
    :param player_id: ID игрока, для которого создается клавиатура.
    :return: Объект ReplyKeyboardMarkup с игровым полем и кнопкой сдаться.
    """
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


def current_game_menu() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру со списком всех активных игр.
    Добавляет кнопки:
    - Новая игра
    - Обновить список игр
    - Главное меню
    """
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


def rating_menu() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру меню рейтинга с кнопками:
    - О рейтинге
    - Главное меню
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ℹ️ О рейтинге")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard


def enemy_board_keyboard(game_id: str, opponent_id: int) -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру с игровым полем соперника для отображения пользователю.
    Отображает клетки с состояниями: попадание, промах или координаты.
    Добавляет кнопку 'Сдаться'.

    :param game_id: ID текущей игры.
    :param opponent_id: ID соперника (для отображения его поля).
    :return: Объект ReplyKeyboardMarkup с игровым полем соперника и кнопкой сдаться.
    """
    board = games[game_id]['boards'][opponent_id]
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
                     [
                         KeyboardButton(text=(cell if cell in ["❌", "💥"] else f"{chr(65 + row)}{col + 1}"))
                         for col, cell in enumerate(board[row])
                     ]
                     for row in range(10)
                 ] + [
                     [KeyboardButton(text="🏳️ Сдаться")]
                 ],
    )
    return keyboard
