from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from app.keyboards import main_menu, back_to_main_menu
from app.logger import setup_logger
from app.services.player_service import register_or_update_player
from app.dependencies import db_session
from app.messages.texts import START_MESSAGE, GAME_RULES

logger = setup_logger(__name__)


async def start_command(message: Message) -> None:
    """
    Обрабатывает команду /start или кнопку '🏠 Главное меню'.
    - Регистрирует или обновляет информацию об игроке.
    - Отправляет приветственное сообщение с клавиатурой главного меню.

    :param message: Объект входящего сообщения от пользователя.
    """
    logger.info(f"👋 Игрок @{message.from_user.username} запустил бота!")

    with db_session() as db:
        register_or_update_player(db, telegram_id=str(message.from_user.id), username=message.from_user.username)

    await message.answer(START_MESSAGE, reply_markup=main_menu(), parse_mode="HTML", disable_web_page_preview=True)


async def show_rules_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает callback-запрос на отображение правил игры.
    - Логирует запрос пользователя.
    - Отправляет текст с правилами игры.

    :param callback: Объект callback-запроса от пользователя.
    """
    logger.info(f"🚓 Игрок @{callback.from_user.username} запросил правила игры!")
    try:
        await callback.answer()
    except Exception:
        pass
    await callback.message.edit_text(GAME_RULES, parse_mode="HTML", reply_markup=back_to_main_menu())


async def main_menu_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает callback-запрос возврата в главное меню.
    - Регистрирует или обновляет информацию об игроке.
    - Отправляет приветственное сообщение с клавиатурой главного меню.

    :param callback: Объект callback-запроса от пользователя.
    """
    logger.info(f"👋 Игрок @{callback.from_user.username} вернулся в главное меню!")

    try:
        await callback.answer()
    except Exception:
        pass

    with db_session() as db:
        register_or_update_player(db, telegram_id=str(callback.from_user.id), username=callback.from_user.username)

    await callback.message.edit_text(START_MESSAGE, reply_markup=main_menu(), parse_mode="HTML",
                                     disable_web_page_preview=True)


def register_handler(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики команд и кнопок:
    - /start — запуск бота
    - '🏠 Главное меню' — возврат в главное меню (для обратной совместимости)
    - '🚓 Правила игры' — показ правил игры (для обратной совместимости)
    - Callback-обработчики для inline-кнопок

    :param dp: Объект диспетчера aiogram.
    """
    # Обработчик команды /start
    dp.message.register(start_command, Command("start"))

    # Callback-обработчики для inline-кнопок
    dp.callback_query.register(main_menu_callback, lambda c: c.data == "main_menu")
    dp.callback_query.register(show_rules_callback, lambda c: c.data == "show_rules")
