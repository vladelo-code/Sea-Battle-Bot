import asyncio
from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.keyboards import broadcast_menu, broadcast_confirm_menu, back_to_main_menu
from app.logger import setup_logger
from app.config import ADMIN_ID
from app.dependencies import db_session
from app.models.player import Player
from sqlalchemy import select

logger = setup_logger(__name__)

# Хранилище для сообщения рассылки и состояния админов
broadcast_message = None
admin_broadcast_state = {}  # {user_id: True/False} - находится ли админ в режиме создания рассылки
admin_creation_message = {}  # {user_id: message} - сообщение "Создание рассылки" для каждого админа


async def is_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором.
    
    :param user_id: ID пользователя
    :return: True если пользователь админ, False иначе
    """
    return str(user_id) == ADMIN_ID


async def broadcast_menu_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает переход в меню рассылки.
    Показывается только администратору.
    
    :param callback: Объект callback-запроса от пользователя.
    """
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав для доступа к этой функции!", show_alert=True)
        return
    
    logger.info(f"📢 Админ @{callback.from_user.username} открыл меню рассылки")
    
    try:
        await callback.answer()
    except Exception:
        pass
    
    await callback.message.edit_text(
        "📢 <b>Меню рассылки</b>\n\n"
        "Здесь вы можете отправить сообщение всем зарегистрированным пользователям бота.\n\n"
        "Нажмите 'Новое сообщение' чтобы создать рассылку.",
        reply_markup=broadcast_menu(),
        parse_mode="HTML"
    )


async def new_message_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает создание нового сообщения для рассылки.
    
    :param callback: Объект callback-запроса от пользователя.
    """
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав для доступа к этой функции!", show_alert=True)
        return
    
    logger.info(f"📝 Админ @{callback.from_user.username} создает новое сообщение для рассылки")
    
    # Устанавливаем состояние создания рассылки для админа
    admin_broadcast_state[callback.from_user.id] = True
    
    try:
        await callback.answer()
    except Exception:
        pass
    
    # Сохраняем ссылку на сообщение "Создание рассылки"
    message = await callback.message.edit_text(
        "📝 <b>Создание рассылки</b>\n\n"
        "Отправьте мне сообщение, которое хотите разослать всем пользователям.\n\n"
        "Сообщение будет отправлено с очисткой всех клавиатур и предложением начать игру командой /start",
        reply_markup=back_to_main_menu(),
        parse_mode="HTML"
    )
    
    # Сохраняем ссылку на сообщение для последующего обновления
    admin_creation_message[callback.from_user.id] = message


async def handle_broadcast_message(message: Message) -> None:
    """
    Обрабатывает сообщение для рассылки от администратора.
    Срабатывает только если пользователь находится в режиме создания рассылки.
    
    :param message: Сообщение от администратора
    """
    if not await is_admin(message.from_user.id):
        return
    
    # Проверяем, что пользователь находится в режиме создания рассылки
    if not admin_broadcast_state.get(message.from_user.id, False):
        return
    
    global broadcast_message
    broadcast_message = message.text
    
    # Сбрасываем состояние создания рассылки
    admin_broadcast_state[message.from_user.id] = False
    
    logger.info(f"📝 Админ @{message.from_user.username} подготовил сообщение для рассылки: {message.text[:50]}...")
    
    # Удаляем кнопку "В главное меню" из исходного сообщения "Создание рассылки"
    try:
        creation_message = admin_creation_message.get(message.from_user.id)
        if creation_message:
            await creation_message.edit_text(
                "📝 <b>Создание рассылки</b>\n\n"
                "Отправьте мне сообщение, которое хотите разослать всем пользователям.\n\n"
                "Сообщение будет отправлено с очисткой всех клавиатур и предложением начать игру командой /start",
                reply_markup=None,
                parse_mode="HTML"
            )
            # Очищаем ссылку на сообщение
            del admin_creation_message[message.from_user.id]
    except Exception as e:
        logger.warning(f"Не удалось обновить исходное сообщение: {e}")
    
    await message.answer(
        f"📝 <b>Сообщение подготовлено</b>\n\n"
        f"<b>Текст рассылки:</b>\n{message.text}\n\n"
        f"Нажмите 'Отправить всем' чтобы разослать это сообщение всем пользователям, "
        f"или 'Отменить' чтобы отменить рассылку.",
        reply_markup=broadcast_confirm_menu(),
        parse_mode="HTML"
    )


async def send_broadcast_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает отправку рассылки всем пользователям.
    
    :param callback: Объект callback-запроса от пользователя.
    """
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав для доступа к этой функции!", show_alert=True)
        return
    
    global broadcast_message
    
    if not broadcast_message:
        await callback.answer("❌ Нет сообщения для рассылки!", show_alert=True)
        return
    
    logger.info(f"📢 Админ @{callback.from_user.username} начал рассылку сообщения")
    
    try:
        await callback.answer()
    except Exception:
        pass
    
    # Показываем сообщение о начале рассылки
    await callback.message.edit_text(
        "📢 <b>Рассылка началась</b>\n\n"
        "Сообщение отправляется всем пользователям...\n"
        "Это может занять некоторое время.",
        parse_mode="HTML"
    )
    
    # Получаем всех пользователей из базы данных
    with db_session() as db:
        result = db.execute(select(Player.telegram_id))
        user_ids = [row[0] for row in result.fetchall()]
    
    total_users = len(user_ids)
    successful_sends = 0
    failed_sends = 0
    
    logger.info(f"📊 Начинаем рассылку для {total_users} пользователей")
    
    # Отправляем сообщения с ограничением скорости
    for i, user_id in enumerate(user_ids):
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=f"{broadcast_message}\n\n"
                     f"🎮 <b>Начните играть командой /start</b>",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )
            successful_sends += 1
            
            # Ограничиваем скорость отправки (1 сообщение в секунду)
            if i < total_users - 1:  # Не ждем после последнего сообщения
                await asyncio.sleep(1)
                
        except TelegramForbiddenError:
            # Пользователь заблокировал бота
            failed_sends += 1
            logger.warning(f"❌ Пользователь {user_id} заблокировал бота")
            
        except TelegramBadRequest as e:
            # Другие ошибки API
            failed_sends += 1
            logger.error(f"❌ Ошибка при отправке пользователю {user_id}: {e}")
            
        except Exception as e:
            # Неожиданные ошибки
            failed_sends += 1
            logger.error(f"❌ Неожиданная ошибка при отправке пользователю {user_id}: {e}")
    
    # Сбрасываем сообщение рассылки и очищаем ссылку на сообщение "Создание рассылки"
    broadcast_message = None
    if callback.from_user.id in admin_creation_message:
        del admin_creation_message[callback.from_user.id]
    
    # Показываем результат
    await callback.message.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Всего пользователей: {total_users}\n"
        f"• Успешно отправлено: {successful_sends}\n"
        f"• Ошибок: {failed_sends}\n\n"
        f"Рассылка завершена успешно!",
        reply_markup=back_to_main_menu(),
        parse_mode="HTML"
    )
    
    logger.info(f"📊 Рассылка завершена: {successful_sends}/{total_users} успешно")


async def cancel_broadcast_callback(callback: CallbackQuery) -> None:
    """
    Обрабатывает отмену рассылки.
    
    :param callback: Объект callback-запроса от пользователя.
    """
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав для доступа к этой функции!", show_alert=True)
        return
    
    global broadcast_message
    broadcast_message = None
    
    # Очищаем ссылку на сообщение "Создание рассылки"
    if callback.from_user.id in admin_creation_message:
        del admin_creation_message[callback.from_user.id]
    
    logger.info(f"❌ Админ @{callback.from_user.username} отменил рассылку")
    
    try:
        await callback.answer()
    except Exception:
        pass
    
    await callback.message.edit_text(
        "❌ <b>Рассылка отменена</b>\n\n"
        "Сообщение не было отправлено пользователям.",
        reply_markup=back_to_main_menu(),
        parse_mode="HTML"
    )


def register_handler(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики для рассылки.
    
    :param dp: Объект диспетчера aiogram.
    """
    # Callback-обработчики
    dp.callback_query.register(broadcast_menu_callback, lambda c: c.data == "broadcast_menu")
    dp.callback_query.register(new_message_callback, lambda c: c.data == "new_broadcast_message")
    dp.callback_query.register(send_broadcast_callback, lambda c: c.data == "send_broadcast")
    dp.callback_query.register(cancel_broadcast_callback, lambda c: c.data == "cancel_broadcast")
    
    # Обработчик текстовых сообщений для рассылки (только для админов в режиме создания рассылки)
    dp.message.register(handle_broadcast_message, lambda m: m.text and not m.text.startswith('/') and str(m.from_user.id) == ADMIN_ID)
