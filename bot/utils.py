import os
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

async def send_admin_notification(bot, booking_id, price):
    """Отправка уведомления администратору о новой оплате"""
    admin_id = os.getenv('ADMIN_TELEGRAM_ID')
    
    if not admin_id:
        logging.error("ADMIN_TELEGRAM_ID не задан в переменных окружения")
        return
    
    try:
        admin_id = int(admin_id)
    except ValueError:
        logging.error(f"ADMIN_TELEGRAM_ID должен быть числом, получено: {admin_id}")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_payment_{booking_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_payment_{booking_id}")
        ]
    ])
    
    try:
        await bot.send_message(
            admin_id,
            f"🆕 <b>Новая оплата!</b>\n\n"
            f"📋 ID заявки: {booking_id}\n"
            f"💰 Сумма: {price}₽\n\n"
            f"Чек приложен к заявке.\n"
            f"Нажмите кнопку для подтверждения.",
            reply_markup=kb,
            parse_mode="HTML"
        )
        logging.info(f"Уведомление отправлено администратору {admin_id}")
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления администратору: {e}")

async def send_notification_to_user(bot, user_id, message):
    """Отправка уведомления пользователю"""
    try:
        await bot.send_message(user_id, message, parse_mode="HTML")
        logging.info(f"Уведомление отправлено пользователю {user_id}")
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")