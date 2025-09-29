from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app.storage import games


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру главного меню с основными командами:
    - Новая игра
    - Присоединиться к игре
    - Мой профиль
    - Рейтинг
    - Рекорды игры
    - Аналитика игр с ботом
    - Рассылка (только для админа)
    
    :param is_admin: Показывать ли кнопку рассылки для администратора
    """
    keyboard_buttons = [
        [InlineKeyboardButton(text="🚀 Новая игра", callback_data="new_game")],
        [InlineKeyboardButton(text="📎 Присоединиться к игре", callback_data="join_game")],
        [InlineKeyboardButton(text="🤖 Игра с ботом", callback_data="play_vs_bot")],
        [InlineKeyboardButton(text="🚓 Правила игры", callback_data="show_rules")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="🥇 Рейтинг", callback_data="rating")],
        [InlineKeyboardButton(text="🎖️ Рекорды игры", callback_data="show_records")],
        [InlineKeyboardButton(text="📈 Аналитика игр с ботом", callback_data="bot_analytics")]
    ]
    
    # Добавляем кнопку рассылки только для администратора
    if is_admin:
        keyboard_buttons.append([InlineKeyboardButton(text="📢 Рассылка", callback_data="broadcast_menu")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return keyboard


def bot_difficulty_menu() -> InlineKeyboardMarkup:
    """
    Меню выбора сложности игры против бота:
    - Простой
    - Средний
    - Сложный
    - В главное меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Простой", callback_data="bot_easy")],
            [InlineKeyboardButton(text="🟡 Средний", callback_data="bot_medium")],
            [InlineKeyboardButton(text="🔴 Сложный", callback_data="bot_hard")],
            [InlineKeyboardButton(text="📈 Аналитика игр с ботом", callback_data="bot_analytics")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")],
        ]
    )
    return keyboard


def after_game_menu() -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру после-игрового меню с основными командами:
    - Сыграть в музыкальном боте
    - Новая игра
    - Присоединиться к игре
    - Главное меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎸 Сыграть в музыкального бота", url="https://t.me/song_sniper_bot")],
            [InlineKeyboardButton(text="🚀 Новая игра", callback_data="new_game")],
            [InlineKeyboardButton(text="📎 Присоединиться к игре", callback_data="join_game")],
            [InlineKeyboardButton(text="🤖 Игра с ботом", callback_data="play_vs_bot")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def connect_menu() -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру для меню подключения к игре:
    - Присоединиться к игре
    - Главное меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📎 Присоединиться к игре", callback_data="join_game")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
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


def current_game_menu() -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру со списком всех активных игр.
    Добавляет кнопки:
    - Новая игра
    - Обновить список игр
    - Главное меню
    """
    keyboard_buttons = []

    # Добавляем кнопки с ID игр
    for game in games:
        keyboard_buttons.append([InlineKeyboardButton(text=f"{game}", callback_data=f"join_game_{game}")])

    # Добавляем навигационные кнопки
    keyboard_buttons.extend([
        [InlineKeyboardButton(text="🚀 Новая игра", callback_data="new_game")],
        [InlineKeyboardButton(text="🔃 Обновить список игр", callback_data="refresh_games")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return keyboard


def rating_menu() -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру меню рейтинга с кнопками:
    - О рейтинге
    - Главное меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ℹ️ О рейтинге", callback_data="about_rating")],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def back_to_main_menu() -> InlineKeyboardMarkup:
    """
    Создает простую inline-клавиатуру с кнопкой возврата в главное меню.
    Используется в различных местах, где нужна только эта кнопка.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard

def bot_analytic_menu() -> InlineKeyboardMarkup:
    """
    Создает простую inline-клавиатуру с кнопками:
    - Игра с ботом
    - Главное меню.
    Используется в меню аналитики игр с ботом.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Игра с ботом", callback_data="play_vs_bot")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
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


def broadcast_menu() -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру меню рассылки:
    - Новое сообщение
    - Главное меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Новое сообщение", callback_data="new_broadcast_message")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def broadcast_confirm_menu() -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру подтверждения рассылки:
    - Отправить всем
    - Отменить
    - Главное меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Отправить всем", callback_data="send_broadcast")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_broadcast")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard
