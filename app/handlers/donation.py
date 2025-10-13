from aiogram import Dispatcher
from aiogram.types import CallbackQuery, PreCheckoutQuery, Message, LabeledPrice

from app.keyboards import donation_menu, back_to_main_menu, donation_cancel_keyboard
from app.dependencies import db_session
from app.db_utils.player import get_or_create_player
from app.db_utils.donor import is_donor, handle_donation
from app.messages.texts import (DONATION_MENU, DONATION_MENU_ALREADY_DONOR,
                                DONATION_SUCCESS, DONATION_ERROR, PROCESS_PAYMENT, DONATION_CANCELLED)
from app.logger import setup_logger

logger = setup_logger("donation")


async def donation_menu_callback(callback: CallbackQuery) -> None:
    """
    Обработчик для показа меню доната.
    """
    logger.info(f"💰 Пользователь @{callback.from_user.username} вошел в меню доната!")

    # Проверяем статус донора
    with db_session() as db:
        donor_status = is_donor(db, callback.from_user.id)

    text = DONATION_MENU_ALREADY_DONOR if donor_status else DONATION_MENU

    try:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=donation_menu()
        )
    except Exception as e:
        logger.error(f"Ошибка в donation_menu_callback: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.")


async def donate_50_stars_callback(callback: CallbackQuery) -> None:
    """
    Обработчик для инициации доната 50 звёзд.
    """
    try:
        logger.info(f"💫 @{callback.from_user.username} инициировал донат 50 ⭐")

        # 1️⃣ Удаляем старое меню (если есть)
        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"Не удалось удалить предыдущее сообщение меню: {e}")

        # 2️⃣ Отправляем инвойс
        invoice_message = await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title="💎 Поддержка проекта «Морской бой»",
            description="Поддержите развитие бота и получите эксклюзивные привилегии!",
            payload="donation_1_star",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Тестовый донат", amount=1)],
            start_parameter="donation_1_star",
        )

        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=PROCESS_PAYMENT,
            parse_mode="HTML",
            reply_markup=donation_cancel_keyboard(invoice_message)
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в donate_50_stars_callback: {e}")
        await callback.answer("Произошла ошибка при создании платежа. Попробуйте позже.")


async def cancel_invoice_callback(callback: CallbackQuery) -> None:
    """
    Обработчик кнопки отмены доната — удаляет инвойс и сообщение.
    """
    try:
        invoice_msg_id = int(callback.data.replace("cancel_invoice_", ""))

        # Удаляем сообщение с инвойсом
        await callback.bot.delete_message(callback.from_user.id, invoice_msg_id)

        # Удаляем сообщение с кнопкой
        await callback.message.delete()

        # Отправляем уведомление
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=DONATION_CANCELLED,
            parse_mode="HTML",
            reply_markup=back_to_main_menu()
        )

        logger.info(f"😔 Пользователь @{callback.from_user.username} отменил инвойс №{invoice_msg_id}")

        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при отмене инвойса: {e}")
        await callback.answer("Не удалось отменить платёж. Попробуйте позже.")


async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery) -> None:
    """
    Обработчик для проверки платежа перед его выполнением.
    """
    try:
        # Проверяем, что это наш платеж
        if pre_checkout_query.invoice_payload == "donation_1_stars":
            await pre_checkout_query.bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=True
            )
        else:
            await pre_checkout_query.bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=False,
                error_message="Неверный платеж"
            )
    except Exception as e:
        logger.error(f"Ошибка в pre_checkout_query_handler: {e}")
        await pre_checkout_query.bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message="Произошла ошибка"
        )


async def successful_payment_handler(message: Message) -> None:
    """
    Универсальный обработчик успешного платежа (любой суммы доната).
    """
    try:
        payload = message.successful_payment.invoice_payload
        if not payload.startswith("donation_"):
            return

        stars_amount = int(payload.replace("donation_", "").replace("_stars", ""))

        with db_session() as db:
            player = get_or_create_player(db, str(message.from_user.id), message.from_user.username)
            handle_donation(db, player, stars_amount, message.successful_payment.date)

        await message.answer(DONATION_SUCCESS, parse_mode="HTML", reply_markup=back_to_main_menu())
        logger.info(f"Пользователь {message.from_user.username} стал донором ({stars_amount} ⭐)")

    except Exception as e:
        logger.error(f"Ошибка в successful_payment_handler: {e}")
        await message.answer(DONATION_ERROR, parse_mode="HTML", reply_markup=back_to_main_menu())


def register_handler(dp: Dispatcher) -> None:
    """
    Регистрирует обработчики для системы доната.
    """
    dp.callback_query.register(donation_menu_callback, lambda c: c.data == "donation_menu")
    dp.callback_query.register(donate_50_stars_callback, lambda c: c.data == "donate_50_stars")
    dp.callback_query.register(cancel_invoice_callback, lambda c: c.data.startswith("cancel_invoice_"))
    dp.pre_checkout_query.register(pre_checkout_query_handler)
    dp.message.register(successful_payment_handler, lambda m: m.successful_payment is not None)
