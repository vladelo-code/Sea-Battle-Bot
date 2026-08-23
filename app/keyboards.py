from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app.storage import games


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру главного меню с основными командами:
    - Новая игра с другом
    - Присоединиться к игре
    - Новая игра с ботом
    - Мой профиль
    - Рейтинг
    - Ачивки
    - Рекорды игры
    – Поддержать проект
    - Рассылка (только для админа)
    
    :param is_admin: Показывать ли кнопку рассылки для администратора
    """
    keyboard_buttons = [
        [InlineKeyboardButton(text="🚀 Новая игра с другом", callback_data="new_game")],
        [InlineKeyboardButton(text="📎 Присоединиться к игре", callback_data="join_game")],
        [InlineKeyboardButton(text="🤖 Новая игра с ботом", callback_data="play_vs_bot")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton(text="🥇 Рейтинг", callback_data="rating")],
        [InlineKeyboardButton(text="🎖 Ачивки", callback_data="achievements_menu")],
        [InlineKeyboardButton(text="🏆 Рекорды игры", callback_data="show_records")],
        [InlineKeyboardButton(text="💎 Поддержать проект", callback_data="donation_menu")],
    ]

    if is_admin:
        keyboard_buttons.append([InlineKeyboardButton(text="📢 Рассылка", callback_data="broadcast_menu")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return keyboard


def bot_difficulty_menu(is_donor: bool = False) -> InlineKeyboardMarkup:
    """
    Меню выбора сложности игры против бота:
    - Простой
    - Средний
    - Сложный
    - Super-Hard (только для доноров)
    - Аналитика игр с ботом
    - Правила игры
    - В главное меню
    """
    keyboard_buttons = [
        [InlineKeyboardButton(text="🟢 Простой", callback_data="bot_easy")],
        [InlineKeyboardButton(text="🟡 Средний", callback_data="bot_medium")],
        [InlineKeyboardButton(text="🔴 Сложный", callback_data="bot_hard")],
    ]

    # Добавляем Super-Hard только для доноров
    if is_donor:
        keyboard_buttons.append([InlineKeyboardButton(text="🔥 Супер-сложный", callback_data="bot_super_hard")])
    else:
        keyboard_buttons.append([InlineKeyboardButton(text="🔥 Супер-сложный", callback_data="donation_menu")])

    keyboard_buttons.extend([
        [InlineKeyboardButton(text="📈 Аналитика игр с ботом", callback_data="bot_analytics")],
        [InlineKeyboardButton(text="🚓 Правила игры", callback_data="show_rules")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")],
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return keyboard


def after_game_menu() -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру после-игрового меню с основными командами:
    - Новая игра с другом
    - Присоединиться к игре
    - Новая игра с ботом
    - Главное меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Новая игра с другом", callback_data="new_game")],
            [InlineKeyboardButton(text="📎 Присоединиться к игре", callback_data="join_game")],
            [InlineKeyboardButton(text="🤖 Новая игра с ботом", callback_data="play_vs_bot")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def connect_menu() -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру для меню подключения к игре:
    - Присоединиться к игре
    - Правила игры
    - Главное меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📎 Присоединиться к игре", callback_data="join_game")],
            [InlineKeyboardButton(text="🚓 Правила игры", callback_data="show_rules")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def playing_menu(game_id: str, player_id: int) -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру с игровым полем для текущего игрока.
    Отображает клетки с состояниями: попадание, промах или координаты.
    Добавляет кнопки 'Сдаться' и 'Пожаловаться на игрока'.

    :param game_id: ID текущей игры.
    :param player_id: ID игрока, для которого создается клавиатура.
    :return: Объект ReplyKeyboardMarkup с игровым полем и кнопками.
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
                     [KeyboardButton(text="🏳️ Сдаться"), KeyboardButton(text="⚠️ Пожаловаться на бездействие")]
                 ],
    )
    return keyboard


def current_game_menu(user_id: int | None = None) -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру со списком всех активных игр.
    Добавляет кнопки:
    - Новая игра с другом
    - Обновить список игр
    - Правила игры
    - Главное меню
    """
    keyboard_buttons = []

    # Добавляем кнопки только с доступными для подключения играми
    for gid, game in games.items():
        # Пропускаем игры, где уже есть два игрока
        if game.get("player1") and game.get("player2") and not game.get("is_bot_game"):
            continue

        # Пропускаем собственные игры пользователя (если передан user_id)
        if user_id is not None and user_id == game.get("player1"):
            continue

        # В меню присоединения показываем только PvP-игры, где есть только первый игрок
        if not game.get("is_bot_game") and game.get("player1") and not game.get("player2"):
            keyboard_buttons.append([InlineKeyboardButton(text=f"{gid}", callback_data=f"join_game_{gid}")])

    # Добавляем навигационные кнопки
    keyboard_buttons.extend([
        [InlineKeyboardButton(text="🚀 Новая игра с другом", callback_data="new_game")],
        [InlineKeyboardButton(text="🔃 Обновить список игр", callback_data="refresh_games")],
        [InlineKeyboardButton(text="🚓 Правила игры", callback_data="show_rules")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return keyboard


def rating_menu() -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру меню рейтинга с кнопками:
    - О рейтинге
    - Мой профиль
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


def profile_menu() -> InlineKeyboardMarkup:
    """
    Создает простую inline-клавиатуру с кнопками:
    - Рейтинг
    - Аналитика игр с ботом
    - Главное меню.
    Используется в меню «Мой профиль» игр с ботом.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🥇 Рейтинг", callback_data="rating")],
            [InlineKeyboardButton(text="📈 Аналитика игр с ботом", callback_data="bot_analytics")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def bot_analytic_menu() -> InlineKeyboardMarkup:
    """
    Создает простую inline-клавиатуру с кнопками:
    - Новая игра с ботом
    - Главное меню.
    Используется в меню аналитики игр с ботом.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Новая игра с ботом", callback_data="play_vs_bot")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def achievements_menu() -> InlineKeyboardMarkup:
    """
    Создает простую inline-клавиатуру с кнопками:
    - Новая игра с другом
    - Присоединиться к игре
    - Новая игра с ботом
    - У меня не работает ачивка...
    - Главное меню.
    Используется в меню ачивок.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Новая игра с другом", callback_data="new_game")],
            [InlineKeyboardButton(text="📎 Присоединиться к игре", callback_data="join_game")],
            [InlineKeyboardButton(text="🤖 Новая игра с ботом", callback_data="play_vs_bot")],
            [InlineKeyboardButton(text="🤬 У меня не работает ачивка...", url="https://t.me/vladelo")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def enemy_board_keyboard(game_id: str, opponent_id: int) -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру с игровым полем соперника для отображения пользователю.
    Отображает клетки с состояниями: попадание, промах или координаты.
    Добавляет кнопки 'Сдаться' и 'Пожаловаться на игрока'.

    :param game_id: ID текущей игры.
    :param opponent_id: ID соперника (для отображения его поля).
    :return: Объект ReplyKeyboardMarkup с игровым полем соперника и кнопками.
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
                     [KeyboardButton(text="🏳️ Сдаться"), KeyboardButton(text="⚠️ Пожаловаться на бездействие")]
                 ],
    )
    return keyboard


def broadcast_menu() -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру меню рассылки:
    - Новое сообщение
    - Посмотреть логи
    - Посмотреть БД
    - Главное меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Новое сообщение", callback_data="new_broadcast_message")],
            [InlineKeyboardButton(text="🗄️ Посмотреть логи", callback_data="check_logs")],
            [InlineKeyboardButton(text="🗄️ Посмотреть БД", callback_data="check_db")],
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


def donation_menu() -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру меню доната:
    - Поддержать 50 звёзд
    - Главное меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌟 Поддержать за 50 звёзд", callback_data="donate_50_stars")],
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def donation_cancel_keyboard(invoice_message) -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру меню доната:
    - Поддержать 50 звёзд
    - Главное меню
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_invoice_{invoice_message.message_id}")]
        ]
    )
    return keyboard
