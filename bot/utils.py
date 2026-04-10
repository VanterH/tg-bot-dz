# bot/utils.py
import os
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)


async def send_admin_notification(bot, entity_id, amount, entity_type):
    """
    Отправка уведомления администратору о новой оплате
    
    Args:
        bot: экземпляр бота
        entity_id: ID записи (booking_id или payment_id)
        amount: сумма оплаты
        entity_type: тип оплаты ("booking" - консультация, "payment" - вопросы)
    """
    admin_id = os.getenv('ADMIN_TELEGRAM_ID')
    
    if not admin_id:
        logging.error("ADMIN_TELEGRAM_ID не задан в переменных окружения")
        return
    
    try:
        admin_id = int(admin_id)
    except ValueError:
        logging.error(f"ADMIN_TELEGRAM_ID должен быть числом, получено: {admin_id}")
        return
    
    if entity_type == "booking":
        text = (
            f"🆕 <b>Новая оплата за консультацию!</b>\n\n"
            f"📋 ID записи: {entity_id}\n"
            f"💰 Сумма: {amount}₽\n\n"
            f"Чек приложен к заявке.\n"
            f"Нажмите кнопку для подтверждения."
        )
        callback_prefix = "confirm_booking"
    else:
        text = (
            f"🆕 <b>Новая оплата вопросов эксперту!</b>\n\n"
            f"📋 ID платежа: {entity_id}\n"
            f"💰 Сумма: {amount}₽\n\n"
            f"Нажмите кнопку для подтверждения."
        )
        callback_prefix = "confirm_payment"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"{callback_prefix}_{entity_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{callback_prefix}_{entity_id}")
        ]
    ])
    
    try:
        await bot.send_message(
            admin_id,
            text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        logging.info(f"Уведомление об оплате отправлено администратору {admin_id}")
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления администратору: {e}")


# bot/utils.py - обновите функцию send_expert_notification

async def send_expert_notification(bot, question_id, question_text, rag_answer, sources, confidence, auto_answered=False):
    """Отправка уведомления эксперту о новом вопросе"""
    expert_ids = os.getenv('EXPERT_TELEGRAM_IDS', '')
    
    if not expert_ids:
        logging.warning("EXPERT_TELEGRAM_IDS не задан в .env")
        return
    
    expert_list = [int(x.strip()) for x in expert_ids.split(',') if x.strip()]
    
    if not expert_list:
        logging.warning("Нет валидных ID экспертов")
        return
    
    # Формируем сообщение и клавиатуру в зависимости от ситуации
    if auto_answered:
        # Вопрос уже отвечен ИИ, но эксперту нужно показать для информации
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Дополнить ответ", callback_data=f"supplement_question_{question_id}")],
            [InlineKeyboardButton(text="📋 Открыть в админке", url=f"http://localhost:8000/question_detail/{question_id}")]
        ])
        message_text = (
            f"🤖 <b>Вопрос #{question_id} обработан ИИ</b>\n\n"
            f"👤 <b>Пользователь:</b> {question_text.split('Тема:')[1].split('Описание:')[0].strip() if 'Тема:' in question_text else '?'}\n\n"
            f"❓ <b>Вопрос:</b>\n{question_text[:400]}...\n\n"
            f"💬 <b>Ответ ИИ:</b>\n{rag_answer[:500]}...\n\n"
            f"📊 <b>Уверенность:</b> {int(confidence * 100)}%\n\n"
            f"<i>Нажмите «Дополнить ответ», чтобы добавить комментарий или уточнить информацию.</i>"
        )
    else:
        # Требуется ручная обработка
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Утвердить", callback_data=f"approve_question_{question_id}"),
                InlineKeyboardButton(text="✏️ Уточнить", callback_data=f"revise_question_{question_id}")
            ],
            [
                InlineKeyboardButton(text="📝 Свой ответ", callback_data=f"custom_question_{question_id}"),
                InlineKeyboardButton(text="📋 Открыть в админке", url=f"http://localhost:8000/question_detail/{question_id}")
            ]
        ])
        message_text = (
            f"📋 <b>Новый вопрос #{question_id}</b>\n\n"
            f"👤 <b>Пользователь:</b> {question_text.split('Тема:')[1].split('Описание:')[0].strip() if 'Тема:' in question_text else '?'}\n\n"
            f"❓ <b>Вопрос:</b>\n{question_text[:500]}...\n\n"
            f"🤖 <b>Предварительный ответ ИИ:</b>\n{rag_answer[:500]}...\n\n"
            f"📊 <b>Уверенность:</b> {int(confidence * 100)}%\n\n"
            f"Выберите действие:"
        )
    
    # Отправляем уведомление каждому эксперту
    for expert_id in expert_list:
        try:
            await bot.send_message(
                expert_id,
                message_text,
                parse_mode="HTML",
                reply_markup=kb
            )
            logging.info(f"Уведомление отправлено эксперту {expert_id}")
        except Exception as e:
            logging.error(f"Ошибка отправки эксперту {expert_id}: {e}")


async def send_user_notification(bot, user_id, message_text, parse_mode="HTML"):
    """Отправка уведомления пользователю"""
    try:
        await bot.send_message(user_id, message_text, parse_mode=parse_mode)
        logging.info(f"Уведомление отправлено пользователю {user_id}")
        return True
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
        return False


async def send_payment_confirmation(bot, user_id, plan, questions_count, valid_until):
    """Отправка подтверждения оплаты вопросов пользователю"""
    message = (
        f"✅ <b>Оплата подтверждена!</b>\n\n"
        f"📦 Тариф: {plan}\n"
        f"❓ Доступно вопросов: {questions_count}\n"
        f"⏰ Действует до: {valid_until.strftime('%d.%m.%Y %H:%M') if valid_until else 'без ограничений'}\n\n"
        f"Теперь вы можете задавать вопросы с помощью кнопки «❓ Задать вопрос эксперту»."
    )
    return await send_user_notification(bot, user_id, message)


async def send_booking_confirmation(bot, user_id, booking_id, service_name, consultation_time):
    """Отправка подтверждения записи на консультацию"""
    message = (
        f"✅ <b>Запись на консультацию подтверждена!</b>\n\n"
        f"📋 ID записи: {booking_id}\n"
        f"📅 Услуга: {service_name}\n"
        f"⏰ Время: {consultation_time.strftime('%d.%m.%Y %H:%M') if consultation_time else 'будет назначено'}\n\n"
        f"Вы получите напоминание за 24 часа."
    )
    return await send_user_notification(bot, user_id, message)


async def send_answer_notification(bot, user_id, question_id, answer):
    """Отправка уведомления о готовом ответе на вопрос"""
    message = (
        f"✅ <b>Ответ на ваш вопрос готов!</b>\n\n"
        f"📋 ID вопроса: {question_id}\n\n"
        f"💬 <b>Ответ:</b>\n"
        f"{answer[:500]}\n\n"
        f"Используйте /archive для просмотра всех ответов."
    )
    return await send_user_notification(bot, user_id, message)


async def send_clarification_request(bot, user_id, question_id, clarification_text):
    """Отправка запроса на уточнение от эксперта"""
    message = (
        f"❓ <b>Эксперт запросил уточнение</b>\n\n"
        f"📋 ID вопроса: {question_id}\n\n"
        f"{clarification_text}\n\n"
        f"Пожалуйста, отправьте дополнительную информацию в этот чат."
    )
    return await send_user_notification(bot, user_id, message)


async def send_error_notification(bot, error_message):
    """Отправка уведомления об ошибке администратору"""
    admin_id = os.getenv('ADMIN_TELEGRAM_ID')
    
    if not admin_id:
        return
    
    try:
        await bot.send_message(
            int(admin_id),
            f"⚠️ <b>Ошибка в системе</b>\n\n"
            f"{error_message}\n\n"
            f"Время: {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
            parse_mode="HTML"
        )
        logging.info("Уведомление об ошибке отправлено администратору")
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления об ошибке: {e}")