from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from app.dependencies import db_session
from app.db_utils.player import get_player_by_telegram_id
from app.services.achievements_service import get_player_achievements
from app.keyboards import achievements_menu
from app.messages.texts import NOT_REGISTERED_MESSAGE
from app.logger import setup_logger

logger = setup_logger(__name__)


def _format_achievements(items: list[dict]) -> str:
    """
    Форматирует список ачивок в читаемый текст для Telegram-сообщения.

    Args:
        items (list[dict]): Список словарей с информацией об ачивках.
            Каждый элемент содержит поля:
              - code (str): системное имя ачивки.
              - title (str): название ачивки.
              - description (str): описание.
              - is_unlocked (bool): получена ли ачивка.
              - percentage (float): процент игроков с этой ачивкой.

    Returns:
        str: Сформированная строка с ачивками, готовая для отправки пользователю.
    """
    lines = ["🎖 <b>Ачивки Морского Боя</b>"]
    for idx, i in enumerate(items, start=1):
        mark = "✅" if i.get("is_unlocked") else "❌"
        title = i.get("title") or i.get("code")
        desc = i.get("description") or ""
        percentage = i.get("percentage", 0.0)
        
        lines.append(f"\n<b>{idx}. {title}</b> — {mark}")
        lines.append(f"{desc}")
        lines.append(f"📊 <i>У {percentage}% игроков уже есть эта ачивка</i>")
    return "\n".join(lines)


async def achievements_menu_callback(callback: CallbackQuery) -> None:
    """
    Хендлер для показа меню ачивок игрока.

    При нажатии на кнопку "Ачивки" бот:
      1. Проверяет регистрацию игрока.
      2. Получает список ачивок и их статус из базы.
      3. Отправляет пользователю форматированный список.

    Args:
        callback (CallbackQuery): Объект колбэка от Telegram.
    """
    logger.info(f"🎖 Игрок @{callback.from_user.username} запросил ачивки!")
    try:
        await callback.answer()
    except Exception:
        pass

    with db_session() as db:
        player = get_player_by_telegram_id(db, str(callback.from_user.id))
        if not player:
            await callback.message.edit_text(NOT_REGISTERED_MESSAGE, reply_markup=achievements_menu())
            return
        items = get_player_achievements(db, callback.from_user.id)

    text = _format_achievements(items)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=achievements_menu())


def register_handler(dp: Dispatcher) -> None:
    """
    Регистрирует хендлер меню ачивок в диспетчере Aiogram.

    Args:
        dp (Dispatcher): Диспетчер бота, к которому прикрепляется хендлер.
    """
    dp.callback_query.register(achievements_menu_callback, lambda c: c.data == "achievements_menu")
