# bot/handlers.py
import os
import logging
import re
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, FSInputFile
from database.db import SessionLocal
from database.models import User, Service, Booking, ScheduleSlot, Question, PaymentRequest, ArchiveEntry, ProductDictionary
from bot.rag_engine import rag_engine
from bot.utils import send_admin_notification, send_expert_notification, send_user_notification
from bot.keyboards import main_menu, services_menu, payment_button, slots_list, slots_button, cancel_button, phone_keyboard, get_topics_keyboard
from aiogram.filters import Command, StateFilter

router = Router()
logging.basicConfig(level=logging.INFO)

# ============ FSM СОСТОЯНИЯ ============
class BookingStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_service = State()
    waiting_for_payment = State()
    waiting_for_screenshot = State()
    waiting_for_slot = State()

class QuestionStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_description = State()
    waiting_for_age_gender = State()
    waiting_for_additional = State()
    waiting_for_clarification = State()

class PaymentStates(StatesGroup):
    waiting_for_plan_selection = State()

class RegistrationStates(StatesGroup):
    waiting_for_email = State()


# ============ КОМАНДА /start ============
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    await state.clear()
    
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        # Новая регистрация
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            language_code=message.from_user.language_code or 'ru'
        )
        session.add(user)
        session.commit()
        
        await message.answer(
            "🌿 Добро пожаловать в бот doTERRA!\n\n"
            "Я могу помочь вам:\n"
            "• 📅 Записаться на консультацию\n"
            "• ❓ Получить консультацию эксперта по эфирным маслам\n\n"
            "Пожалуйста, укажите ваш email для получения уведомлений:",
            reply_markup=cancel_button()
        )
        await state.set_state(RegistrationStates.waiting_for_email)
    else:
        user.last_active = datetime.now()
        session.commit()
        await show_main_menu(message, user)
    
    session.close()

@router.message(RegistrationStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    """Обработка email при регистрации"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Регистрация отменена.", reply_markup=ReplyKeyboardRemove())
        return
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, message.text):
        await message.answer("❌ Пожалуйста, введите корректный email адрес:")
        return
    
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    if user:
        user.email = message.text
        user.last_active = datetime.now()
        session.commit()
    
    session.close()
    await state.clear()
    
    await message.answer(
        "✅ Регистрация завершена!\n\n"
        "🌿 Теперь вы можете пользоваться всеми функциями бота.",
        reply_markup=main_menu()
    )

async def show_main_menu(message: Message, user: User):
    """Показать главное меню с информацией о статусе"""
    session = SessionLocal()
    
    # Проверяем статус подписки для вопросов
    subscription_active = False
    remaining_questions = 0
    if user.subscription_status == 'active' and user.subscription_valid_until and user.subscription_valid_until > datetime.now():
        subscription_active = True
        remaining_questions = user.questions_total - user.questions_used
        questions_text = f"\n❓ Осталось вопросов эксперту: {remaining_questions}"
    else:
        questions_text = "\n❓ Вопросы эксперту: требуется оплата (/pay)"
    
    # Проверяем активные записи на консультацию
    active_bookings = session.query(Booking).filter(
        Booking.user_id == user.id,
        Booking.payment_status == 'paid',
        Booking.consultation_datetime > datetime.now()
    ).count()
    
    bookings_text = f"\n📅 Активных записей на консультацию: {active_bookings}"
    
    await message.answer(
        f"🌿 Здравствуйте, {user.first_name or user.username}!{questions_text}{bookings_text}\n\n"
        f"Выберите действие:",
        reply_markup=main_menu()
    )
    session.close()


# ============ ОТМЕНА ============
@router.message(F.text == "❌ Отмена")
@router.message(Command("cancel"))
async def cancel_operation(message: Message, state: FSMContext):
    """Отмена текущей операции"""
    await state.clear()
    await message.answer(
        "✅ Операция отменена.\n\nВозврат в главное меню:",
        reply_markup=main_menu()
    )


# ============ 1. ЗАПИСЬ НА КОНСУЛЬТАЦИЮ ============

# ============ ЗАПИСЬ НА КОНСУЛЬТАЦИЮ ============

@router.message(F.text == "📅 Запись на консультацию")
async def book_consultation(message: Message, state: FSMContext):
    """Начало записи на консультацию"""
    await state.clear()
    
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    if not user or not user.phone:
        await message.answer(
            "📝 Давайте начнем регистрацию!\n\n"
            "Как вас называть?",
            reply_markup=cancel_button()
        )
        await state.set_state(BookingStates.waiting_for_name)
    else:
        await message.answer(
            f"👋 {user.first_name or user.username}, выберите услугу:",
            reply_markup=services_menu()
        )
        await state.set_state(BookingStates.waiting_for_service)
    
    session.close()


@router.message(BookingStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    """Получение имени пользователя"""
    if message.text == "❌ Отмена":
        await cancel_operation(message, state)
        return
    
    await state.update_data(name=message.text)
    await message.answer(
        "📞 Пожалуйста, отправьте ваш номер телефона:",
        reply_markup=phone_keyboard()
    )
    await state.set_state(BookingStates.waiting_for_phone)


@router.message(BookingStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    """Получение номера телефона"""
    if message.text == "❌ Отмена":
        await cancel_operation(message, state)
        return
    
    # Получаем номер телефона
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text
    
    data = await state.get_data()
    name = data.get('name')
    
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    if user:
        # Обновляем существующего пользователя
        if name:
            user.first_name = name
        user.phone = phone
        user.last_active = datetime.now()
        session.commit()
        print(f"✅ Обновлен пользователь: {user.first_name}, телефон: {user.phone}")
    else:
        # Создаем нового пользователя
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=name,
            phone=phone,
            language_code=message.from_user.language_code or 'ru'
        )
        session.add(user)
        session.commit()
        print(f"✅ Создан пользователь: {user.first_name}, телефон: {user.phone}")
    
    session.close()
    
    # Сохраняем данные в state
    await state.update_data(phone=phone, name=name)
    
    # Отправляем сообщение с выбором услуги
    await message.answer(
        "✅ Номер телефона сохранен!\n\n"
        "Теперь выберите услугу:",
        reply_markup=services_menu()
    )
    await state.set_state(BookingStates.waiting_for_service)


@router.callback_query(F.data.startswith("service_"), BookingStates.waiting_for_service)
async def select_service(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора услуги"""
    service_id = int(callback.data.split("_")[1])
    
    session = SessionLocal()
    service = session.query(Service).get(service_id)
    
    if not service:
        await callback.message.edit_text("❌ Услуга не найдена")
        await callback.answer()
        session.close()
        return
    
    await state.update_data(service_id=service_id, service_price=service.price_rub, service_name=service.name)
    
    # Создаем клавиатуру с кнопкой оплаты
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Я оплатил(а)", callback_data="payment_made")]
    ])
    
    await callback.message.edit_text(
        f"✅ Выбрано: {service.name}\n"
        f"💰 Цена: {service.price_rub}₽\n\n"
        f"После оплаты нажмите кнопку ниже и отправьте скриншот чека:",
        reply_markup=kb
    )
    await state.set_state(BookingStates.waiting_for_payment)
    session.close()
    await callback.answer()


@router.callback_query(F.data == "payment_made", BookingStates.waiting_for_payment)
async def payment_made(callback: CallbackQuery, state: FSMContext):
    """Пользователь нажал 'Я оплатил'"""
    await callback.message.answer(
        "📸 Пожалуйста, отправьте скриншот чека об оплате:",
        reply_markup=cancel_button()
    )
    await state.update_data(waiting_for_screenshot=True)
    await callback.answer()


@router.message(BookingStates.waiting_for_payment, F.photo)
async def receive_screenshot(message: Message, state: FSMContext):
    """Получение скриншота чека"""
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    
    # Сохраняем фото
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/payment_{message.from_user.id}_{datetime.now().timestamp()}.jpg"
    await message.bot.download_file(file.file_path, file_path)
    
    data = await state.get_data()
    
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    booking = Booking(
        user_id=user.id,
        service_id=data['service_id'],
        payment_status='waiting_confirm',
        payment_proof_url=file_path
    )
    session.add(booking)
    session.commit()
    booking_id = booking.id
    session.close()
    
    await message.answer(
        "✅ Чек получен!\n\n"
        "После подтверждения администратором вы сможете выбрать время.\n"
        "Обычно это занимает несколько минут.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Уведомляем администратора
    await send_admin_notification(message.bot, booking_id, data['service_price'], "booking")
    await state.clear()


# ============ ВЫБОР ВРЕМЕНИ ДЛЯ КОНСУЛЬТАЦИИ ============

@router.callback_query(F.data == "choose_slot")
async def choose_slot_callback(callback: CallbackQuery):
    """Обработка нажатия кнопки 'Выбрать время'"""
    session = SessionLocal()
    
    try:
        user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
        
        if not user:
            await callback.message.answer("❌ Пользователь не найден. Начните с /start")
            await callback.answer()
            return
        
        # Проверяем есть ли оплаченная заявка
        booking = session.query(Booking).filter_by(
            user_id=user.id, 
            payment_status='paid'
        ).order_by(Booking.created_at.desc()).first()
        
        if not booking:
            await callback.message.answer("❌ У вас нет подтвержденных оплат. Сначала оплатите услугу.")
            await callback.answer()
            return
        
        # Проверяем не выбрано ли уже время
        if booking.consultation_datetime:
            await callback.message.answer(
                f"⏰ Время уже выбрано!\n\n"
                f"📅 Дата и время: {booking.consultation_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Если хотите изменить время, обратитесь к администратору."
            )
            await callback.answer()
            return
        
        # Получаем свободные слоты
        slots = session.query(ScheduleSlot).filter(
            ScheduleSlot.slot_datetime > datetime.now(),
            ScheduleSlot.is_booked == False
        ).order_by(ScheduleSlot.slot_datetime).limit(10).all()
        
        if not slots:
            await callback.message.answer("❌ Нет доступных слотов для записи. Загляните позже!")
            await callback.answer()
            return
        
        # Создаем клавиатуру со слотами
        keyboard_buttons = []
        for slot in slots:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=slot.slot_datetime.strftime("%d.%m %H:%M"), 
                    callback_data=f"book_slot_{slot.id}"
                )
            ])
        
        # Добавляем кнопку обновления
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔄 Обновить список", callback_data="refresh_slots")
        ])
        
        kb = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            "🗓️ <b>Доступное время для записи:</b>\n\n"
            "Выберите удобное время:",
            reply_markup=kb,
            parse_mode="HTML"
        )
    finally:
        session.close()
    
    await callback.answer()


@router.callback_query(F.data == "refresh_slots")
async def refresh_slots(callback: CallbackQuery):
    """Обновление списка слотов"""
    await choose_slot_callback(callback)


@router.callback_query(F.data.startswith("book_slot_"))
async def book_slot_callback(callback: CallbackQuery):
    """Обработка выбора слота"""
    slot_id = int(callback.data.split("_")[2])
    
    session = SessionLocal()
    
    try:
        slot = session.query(ScheduleSlot).get(slot_id)
        if not slot or slot.is_booked:
            await callback.message.edit_text("❌ Извините, это время уже занято. Выберите другое.")
            await callback.answer()
            return
        
        user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
        if not user:
            await callback.message.answer("❌ Пользователь не найден")
            await callback.answer()
            return
        
        # Находим оплаченную заявку
        booking = session.query(Booking).filter_by(
            user_id=user.id, 
            payment_status='paid'
        ).order_by(Booking.created_at.desc()).first()
        
        if not booking:
            await callback.message.edit_text("❌ Заявка не найдена")
            await callback.answer()
            return
        
        # Проверяем не забронировано ли уже время
        if booking.consultation_datetime:
            await callback.message.edit_text("❌ Вы уже выбрали время для этой записи!")
            await callback.answer()
            return
        
        # Бронируем слот
        slot.is_booked = True
        slot.booking_id = booking.id
        booking.consultation_datetime = slot.slot_datetime
        session.commit()
        
        # Получаем услугу
        service = session.query(Service).get(booking.service_id)
        
        await callback.message.edit_text(
            f"✅ <b>Время успешно забронировано!</b>\n\n"
            f"📅 Дата и время: {slot.slot_datetime.strftime('%d.%m.%Y %H:%M')}\n"
            f"📋 Услуга: {service.name if service else '-'}\n\n"
            f"Вы получите напоминание за 24 часа до консультации.\n\n"
            f"Вернуться в главное меню: /start",
            parse_mode="HTML"
        )
    finally:
        session.close()
    
    await callback.answer()


# ============ МОИ ЗАПИСИ ============

@router.message(F.text == "📋 Мои записи")
async def my_bookings(message: Message):
    """Просмотр своих записей на консультацию"""
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("❌ Пользователь не найден. Отправьте /start")
        session.close()
        return
    
    bookings = session.query(Booking).filter_by(user_id=user.id).order_by(Booking.created_at.desc()).all()
    
    if not bookings:
        await message.answer("📭 У вас пока нет записей.\nНажмите «Запись на консультацию» чтобы создать новую.")
    else:
        text = "📋 <b>Ваши записи на консультацию:</b>\n\n"
        for b in bookings:
            service = session.query(Service).get(b.service_id)
            status_emoji = {
                'pending': '⏳',
                'waiting_confirm': '🟡',
                'paid': '✅',
                'rejected': '❌'
            }.get(b.payment_status, '❓')
            
            text += f"{status_emoji} <b>Запись #{b.id}</b>\n"
            text += f"   Услуга: {service.name if service else '-'}\n"
            text += f"   Статус: {b.payment_status}\n"
            if b.consultation_datetime:
                text += f"   Дата: {b.consultation_datetime.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"   Создана: {b.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        await message.answer(text, parse_mode="HTML")
    
    session.close()


# ============ 2. ВОПРОСЫ ЭКСПЕРТУ (RAG) ============

@router.message(F.text == "❓ Задать вопрос эксперту")
@router.message(Command("ask"))
async def cmd_ask(message: Message, state: FSMContext):
    """Начало процесса задавания вопроса эксперту"""
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("❌ Пользователь не найден. Отправьте /start")
        session.close()
        return
    
    # Проверяем лимиты
    if user.subscription_status != 'active' or (user.subscription_valid_until and user.subscription_valid_until < datetime.now()):
        await message.answer(
            "⚠️ <b>У вас нет активной подписки!</b>\n\n"
            "Используйте кнопку «💳 Пополнить баланс» для выбора тарифа.",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        session.close()
        return
    
    if user.questions_used >= user.questions_total:
        await message.answer(
            f"❌ <b>Вы исчерпали лимит вопросов!</b>\n\n"
            f"Использовано: {user.questions_used}/{user.questions_total}\n\n"
            "Используйте кнопку «💳 Пополнить баланс» для покупки дополнительных вопросов.",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        session.close()
        return
    
    session.close()
    
    await message.answer(
        "🌿 <b>Задайте вопрос эксперту doTERRA</b>\n\n"
        "Выберите тему вопроса:",
        parse_mode="HTML",
        reply_markup=get_topics_keyboard()
    )
    await state.set_state(QuestionStates.waiting_for_topic)

@router.callback_query(F.data.startswith("topic_"), QuestionStates.waiting_for_topic)
async def process_topic(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора темы"""
    topic = callback.data.split("_")[1]
    await state.update_data(topic=topic)
    
    await callback.message.edit_text(
        f"📝 <b>Вы выбрали тему: {topic}</b>\n\n"
        "Опишите вашу ситуацию (2-5 предложений):\n\n"
        "Например:\n"
        "«Меня беспокоит бессонница последние 2 недели, просыпаюсь ночью и не могу заснуть»",
        parse_mode="HTML"
    )
    await state.set_state(QuestionStates.waiting_for_description)
    await callback.answer()

@router.message(QuestionStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания ситуации"""
    if message.text == "❌ Отмена":
        await cancel_operation(message, state)
        return
    
    if len(message.text) < 20:
        await message.answer(
            "❌ Пожалуйста, опишите ситуацию подробнее (минимум 20 символов):\n"
            "Это поможет эксперту дать более точный ответ."
        )
        return
    
    await state.update_data(description=message.text)
    
    await message.answer(
        "👤 <b>Укажите ваш возраст и пол</b>\n\n"
        "Например: 35, женский\n"
        "Или: 42, мужской",
        parse_mode="HTML"
    )
    await state.set_state(QuestionStates.waiting_for_age_gender)

@router.message(QuestionStates.waiting_for_age_gender)
async def process_age_gender(message: Message, state: FSMContext):
    """Обработка возраста и пола"""
    if message.text == "❌ Отмена":
        await cancel_operation(message, state)
        return
    
    await state.update_data(age_gender=message.text)
    
    await message.answer(
        "📝 <b>Дополнительная информация</b>\n\n"
        "Если есть что добавить (хронические заболевания, принимаемые лекарства, аллергии), напишите здесь.\n\n"
        "Или отправьте «Пропустить»",
        parse_mode="HTML"
    )
    await state.set_state(QuestionStates.waiting_for_additional)

@router.message(QuestionStates.waiting_for_additional)
async def process_additional(message: Message, state: FSMContext):
    """Обработка дополнительной информации и отправка вопроса"""
    if message.text == "❌ Отмена":
        await cancel_operation(message, state)
        return
    
    additional = None if message.text == "Пропустить" else message.text
    await state.update_data(additional=additional)
    
    data = await state.get_data()
    
    # Формируем полный текст вопроса
    full_question = f"""
<b>Тема:</b> {data.get('topic')}
<b>Описание:</b> {data.get('description')}
<b>Возраст/пол:</b> {data.get('age_gender')}
<b>Доп. информация:</b> {additional or 'Нет'}
"""
    
    # Сохраняем вопрос в БД
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    # Генерируем ID вопроса
    today = datetime.now().strftime("%Y%m%d")
    last_question = session.query(Question).filter(Question.id.like(f"q_{today}_%")).order_by(Question.id.desc()).first()
    
    if last_question:
        seq = int(last_question.id.split("_")[2]) + 1
    else:
        seq = 1
    
    question_id = f"q_{today}_{seq:03d}"
    
    # Извлекаем возраст
    age = None
    try:
        age_match = re.search(r'(\d+)', data.get('age_gender', ''))
        if age_match:
            age = int(age_match.group(1))
    except:
        pass
    
    # Извлекаем пол
    gender = None
    gender_lower = data.get('age_gender', '').lower()
    if 'жен' in gender_lower or 'female' in gender_lower:
        gender = 'female'
    elif 'муж' in gender_lower or 'male' in gender_lower:
        gender = 'male'
    
    question = Question(
        id=question_id,
        user_id=user.id,
        text=full_question,
        topic=data.get('topic'),
        age=age,
        gender=gender,
        additional_info=additional,
        status='received'
    )
    session.add(question)
    session.commit()
    
    await message.answer(
        f"✅ <b>Ваш вопрос принят!</b>\n\n"
        f"📋 ID вопроса: {question_id}\n\n"
        f"🔄 Формирую ответ...\n\n"
        f"⏳ Обычно это занимает 10-30 секунд.",
        parse_mode="HTML"
    )
    
    # Генерируем RAG-ответ
    try:
        rag_result = await rag_engine.generate_answer(full_question, user.id)
        
        question.rag_answer = rag_result.get('answer')
        question.rag_confidence = rag_result.get('confidence')
        question.rag_sources = rag_result.get('sources')
        
        # 🔴 ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ ЭКСПЕРТУ ВСЕГДА
        await send_expert_notification(
            message.bot,
            question_id,
            full_question,
            rag_result.get('answer'),
            rag_result.get('sources', []),
            rag_result.get('confidence', 0),
            auto_answered=not rag_result.get('needs_clarification', False)
        )
        
        if rag_result.get('needs_clarification'):
            question.status = 'needs_more_info'
            session.commit()
            await message.answer(
                "❓ <b>Для более точного ответа нужна дополнительная информация</b>\n\n"
                f"{rag_result.get('answer')}\n\n"
                "Пожалуйста, отправьте уточнения в этот чат.",
                parse_mode="HTML"
            )
            await state.set_state(QuestionStates.waiting_for_clarification)
            await state.update_data(question_id=question_id)
        else:
            # Отправляем ответ пользователю сразу
            question.status = 'answered'
            question.final_answer = rag_result.get('answer')
            question.answered_at = datetime.now()
            
            # Сохраняем в архив
            archive = ArchiveEntry(
                question_id=question_id,
                user_id=user.id,
                question_text=full_question,
                final_answer=rag_result.get('answer'),
                topics=[data.get('topic')]
            )
            session.add(archive)
            
            # Уменьшаем лимит вопросов
            user.questions_used += 1
            session.commit()
            
            await message.answer(
                f"✅ <b>Ответ на ваш вопрос:</b>\n\n"
                f"{rag_result.get('answer')}\n\n"
                f"📋 ID вопроса: {question_id}\n\n"
                f"Используйте /archive для просмотра всех ответов.",
                parse_mode="HTML"
            )
            await state.clear()
            
    except Exception as e:
        logging.error(f"RAG generation error: {e}")
        question.status = 'expert_review'
        session.commit()
        
        # Отправляем уведомление эксперту об ошибке
        await send_expert_notification(
            message.bot,
            question_id,
            full_question,
            "Ошибка генерации RAG-ответа. Требуется ручная обработка.",
            [],
            0,
            auto_answered=False
        )
        
        await message.answer(
            f"⚠️ <b>Техническая ошибка при формировании ответа</b>\n\n"
            f"Ваш вопрос передан эксперту. Ответ вы получите в течение 24 часов.\n\n"
            f"📋 ID вопроса: {question_id}",
            parse_mode="HTML"
        )
        await state.clear()
    
    session.close()


# ============ ПОПОЛНЕНИЕ БАЛАНСА (ВОПРОСЫ) ============

@router.message(F.text == "💳 Пополнить баланс")
@router.message(Command("pay"))
async def cmd_pay(message: Message, state: FSMContext):
    """Выбор тарифа для оплаты вопросов"""
    tariffs = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 1 вопрос - 299₽ / $3.5", callback_data="pay_one_time")],
        [InlineKeyboardButton(text="🔸 7 вопросов/неделя - 1499₽ / $17", callback_data="pay_week")],
        [InlineKeyboardButton(text="🔹 30 вопросов/месяц - 4999₽ / $55", callback_data="pay_month")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])
    
    await message.answer(
        "💳 <b>Выберите тариф для вопросов эксперту:</b>\n\n"
        "🔹 <b>1 вопрос</b> — 299₽ / $3.5\n"
        "🔸 <b>7 вопросов (неделя)</b> — 1499₽ / $17\n"
        "🔹 <b>30 вопросов (месяц)</b> — 4999₽ / $55\n\n"
        "После оплаты нажмите «Я оплатил», администратор подтвердит платеж.",
        parse_mode="HTML",
        reply_markup=tariffs
    )

@router.callback_query(F.data.startswith("pay_"))
async def process_payment_selection(callback: CallbackQuery):
    """Обработка выбора тарифа"""
    plan = callback.data.split("_")[1]
    
    tariffs = {
        "one_time": {"rub": 299, "usd": 3.5, "questions": 1, "days": 0},
        "week": {"rub": 1499, "usd": 17, "questions": 7, "days": 7},
        "month": {"rub": 4999, "usd": 55, "questions": 30, "days": 30}
    }
    
    tariff = tariffs.get(plan)
    if not tariff:
        await callback.answer("❌ Тариф не найден")
        return
    
    payment_link_rub = f"https://payment.example.com/pay?amount={tariff['rub']}&currency=RUB"
    payment_link_usd = f"https://payment.example.com/pay?amount={tariff['usd']}&currency=USD"
    
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=callback.from_user.id).first()
    
    if user:
        payment_request = PaymentRequest(
            user_id=user.id,
            plan=plan,
            amount_rub=tariff['rub'],
            amount_usd=tariff['usd'],
            questions_count=tariff['questions'],
            valid_days=tariff['days'],
            payment_link=payment_link_rub
        )
        session.add(payment_request)
        session.commit()
        payment_id = payment_request.id
    else:
        payment_id = None
    
    session.close()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить в рублях", url=payment_link_rub)],
        [InlineKeyboardButton(text="💵 Оплатить в долларах", url=payment_link_usd)],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"payment_done_{payment_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        f"💳 <b>Вы выбрали тариф: {plan}</b>\n\n"
        f"💰 Сумма: {tariff['rub']}₽ / ${tariff['usd']}\n"
        f"❓ Вопросов: {tariff['questions']}\n"
        f"⏰ Срок: {'без ограничений' if tariff['days'] == 0 else f'{tariff['days']} дней'}\n\n"
        f"После оплаты нажмите «Я оплатил».",
        parse_mode="HTML",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data.startswith("payment_done_"))
async def payment_done(callback: CallbackQuery):
    """Пользователь нажал 'Я оплатил'"""
    payment_id = int(callback.data.split("_")[2])
    
    session = SessionLocal()
    payment = session.query(PaymentRequest).get(payment_id)
    
    if payment:
        await send_admin_notification(
            callback.bot,
            payment_id,
            payment.amount_rub,
            "payment"
        )
        await callback.message.edit_text(
            "✅ <b>Сообщение отправлено администратору!</b>\n\n"
            "Ожидайте подтверждения оплаты.\n"
            "После подтверждения вы сможете задавать вопросы.",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Ошибка: платеж не найден")
    
    session.close()
    await callback.answer()


# ============ АРХИВ ВОПРОСОВ ============

@router.message(F.text == "📋 Архив вопросов")
@router.message(Command("archive"))
async def cmd_archive(message: Message):
    """Показать архив вопросов"""
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        session.close()
        return
    
    archives = session.query(ArchiveEntry).filter_by(user_id=user.id).order_by(ArchiveEntry.created_at.desc()).limit(10).all()
    
    if not archives:
        await message.answer("📭 У вас пока нет вопросов в архиве.")
    else:
        text = "📋 <b>Архив вопросов:</b>\n\n"
        for a in archives:
            text += f"🔹 <b>Вопрос #{a.question_id}</b>\n"
            text += f"   📅 {a.created_at.strftime('%d.%m.%Y')}\n"
            text += f"   {a.question_text[:100]}...\n"
            text += f"   💬 {a.final_answer[:150]}...\n\n"
        
        await message.answer(text, parse_mode="HTML")
    
    session.close()


# ============ СТАТУС ============

@router.message(F.text == "📊 Мой статус")
@router.message(Command("status"))
async def cmd_status(message: Message):
    """Показать статус пользователя"""
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        session.close()
        return
    
    # Консультации
    active_bookings = session.query(Booking).filter(
        Booking.user_id == user.id,
        Booking.payment_status == 'paid',
        Booking.consultation_datetime > datetime.now()
    ).count()
    
    # Вопросы
    questions_used = user.questions_used
    questions_total = user.questions_total
    subscription_status = "✅ Активна" if user.subscription_status == 'active' and user.subscription_valid_until > datetime.now() else "❌ Не активна"
    
    # Активные вопросы
    active_questions = session.query(Question).filter(
        Question.user_id == user.id,
        Question.status.in_(['expert_review', 'received', 'needs_more_info'])
    ).count()
    
    text = f"""
📊 <b>Ваш статус</b>

👤 <b>Профиль:</b>
• Имя: {user.first_name or user.username}
• Email: {user.email or 'не указан'}

📅 <b>Консультации:</b>
• Активных записей: {active_bookings}

❓ <b>Вопросы эксперту:</b>
• Статус подписки: {subscription_status}
• Использовано вопросов: {questions_used}/{questions_total}
• Действует до: {user.subscription_valid_until.strftime('%d.%m.%Y') if user.subscription_valid_until else 'не указано'}
• Вопросов в обработке: {active_questions}

💡 <i>Используйте кнопки меню для действий</i>
"""
    await message.answer(text, parse_mode="HTML")
    session.close()


# ============ ПОМОЩЬ ============

@router.message(F.text == "ℹ️ Помощь")
@router.message(Command("help"))
async def cmd_help(message: Message):
    """Показать справку"""
    help_text = """
🌿 <b>Помощь по боту doTERRA</b>

<b>📌 Запись на консультацию:</b>
1. Нажмите «Запись на консультацию»
2. Выберите услугу
3. Оплатите и отправьте чек
4. После подтверждения выберите время

<b>❓ Вопрос эксперту:</b>
1. Нажмите «Задать вопрос эксперту»
2. Выберите тему
3. Опишите ситуацию
4. Получите ответ в течение 24 часов

<b>💰 Тарифы на вопросы:</b>
• 1 вопрос — 299₽
• 7 вопросов/неделя — 1499₽
• 30 вопросов/месяц — 4999₽

<b>📞 Контакты:</b>
@doterra_support
"""
    await message.answer(help_text, parse_mode="HTML", reply_markup=main_menu())


# ============ КНОПКА НАЗАД ============

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("🌿 Главное меню:", reply_markup=main_menu())
    await callback.answer()
    
    
# bot/handlers.py - добавьте в конец файла

# ============ ОБРАБОТЧИКИ КНОПОК ЭКСПЕРТА ============

@router.callback_query(F.data.startswith("approve_question_"))
async def expert_approve_question(callback: CallbackQuery):
    """Эксперт утверждает ответ"""
    question_id = callback.data.split("_")[2]
    
    session = SessionLocal()
    question = session.query(Question).get(question_id)
    
    if not question:
        await callback.message.edit_text("❌ Вопрос не найден")
        await callback.answer()
        session.close()
        return
    
    # Проверяем, не отвечен ли уже вопрос
    if question.status == 'answered':
        await callback.message.edit_text("⚠️ Вопрос уже был отвечен")
        await callback.answer()
        session.close()
        return
    
    # Утверждаем RAG ответ
    question.status = 'answered'
    question.final_answer = question.rag_answer
    question.answered_at = datetime.now()
    question.expert_id = callback.from_user.id
    
    # Уменьшаем лимит вопросов у пользователя
    user = session.query(User).get(question.user_id)
    if user and question.status != 'answered':
        user.questions_used += 1
    
    # Сохраняем в архив
    archive = ArchiveEntry(
        question_id=question.id,
        user_id=question.user_id,
        question_text=question.text,
        final_answer=question.rag_answer,
        topics=[question.topic] if question.topic else []
    )
    session.add(archive)
    session.commit()
    
    # Уведомляем пользователя
    if user:
        try:
            await callback.bot.send_message(
                user.telegram_id,
                f"✅ <b>Эксперт подтвердил ответ на ваш вопрос!</b>\n\n"
                f"📋 ID вопроса: {question_id}\n\n"
                f"💬 Ответ:\n{question.rag_answer[:500]}",
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Ошибка отправки пользователю: {e}")
    
    await callback.message.edit_text(f"✅ Вопрос #{question_id} утвержден и отправлен пользователю")
    session.close()
    await callback.answer()


@router.callback_query(F.data.startswith("revise_question_"))
async def expert_revise_question(callback: CallbackQuery, state: FSMContext):
    """Эксперт запрашивает уточнение"""
    question_id = callback.data.split("_")[2]
    
    await state.update_data(question_id=question_id)
    
    await callback.message.answer(
        f"📝 Введите уточнения для вопроса #{question_id}:\n\n"
        "Укажите, какую информацию нужно добавить или уточнить:"
    )
    await state.set_state("waiting_for_revision")
    await callback.answer()


@router.message(F.text, StateFilter("waiting_for_revision"))
async def process_revision(message: Message, state: FSMContext):
    """Обработка уточнений от эксперта"""
    data = await state.get_data()
    question_id = data.get('question_id')
    revision_text = message.text
    
    session = SessionLocal()
    question = session.query(Question).get(question_id)
    
    if question:
        question.expert_revision_notes = revision_text
        question.expert_iterations += 1
        
        if question.expert_iterations >= 2:
            # После 2 итераций - эксперту нужно дать свой ответ
            await message.answer(
                f"⚠️ Достигнуто максимальное количество итераций.\n"
                f"Пожалуйста, напишите свой ответ для вопроса #{question_id}:"
            )
            await state.set_state("waiting_for_custom_answer")
        else:
            # Генерируем новый RAG ответ с учетом уточнений
            await message.answer(f"🔄 Генерация нового ответа с учетом уточнений...")
            
            # Обновляем вопрос с уточнениями
            updated_question = question.text + f"\n\n<b>Уточнения эксперта:</b>\n{revision_text}"
            
            # Генерируем новый RAG ответ
            from bot.rag_engine import rag_engine
            rag_result = await rag_engine.generate_answer(updated_question, question.user_id, revision_text)
            
            question.rag_answer = rag_result.get('answer')
            question.rag_confidence = rag_result.get('confidence')
            question.status = 'expert_review'
            session.commit()
            
            # Отправляем эксперту новый ответ
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Утвердить", callback_data=f"approve_question_{question_id}"),
                    InlineKeyboardButton(text="✏️ Уточнить", callback_data=f"revise_question_{question_id}")
                ],
                [
                    InlineKeyboardButton(text="📝 Свой ответ", callback_data=f"custom_question_{question_id}")
                ]
            ])
            
            await message.answer(
                f"🔄 <b>Обновленный ответ для вопроса #{question_id}</b>\n\n"
                f"{rag_result.get('answer')}\n\n"
                f"Уверенность: {int(rag_result.get('confidence', 0) * 100)}%\n\n"
                f"Выберите действие:",
                parse_mode="HTML",
                reply_markup=kb
            )
            await state.clear()
    
    session.close()


@router.callback_query(F.data.startswith("custom_question_"))
async def expert_custom_answer(callback: CallbackQuery, state: FSMContext):
    """Эксперт пишет свой ответ"""
    question_id = callback.data.split("_")[2]
    
    await state.update_data(question_id=question_id)
    await callback.message.answer(
        f"📝 Введите ваш ответ для вопроса #{question_id}:\n\n"
        "Ответ будет отправлен пользователю:"
    )
    await state.set_state("waiting_for_custom_answer")
    await callback.answer()


@router.message(F.text, StateFilter("waiting_for_custom_answer"))
async def process_custom_answer(message: Message, state: FSMContext):
    """Обработка своего ответа от эксперта"""
    data = await state.get_data()
    question_id = data.get('question_id')
    custom_answer = message.text
    
    session = SessionLocal()
    question = session.query(Question).get(question_id)
    
    if question:
        question.status = 'answered'
        question.final_answer = custom_answer
        question.answered_at = datetime.now()
        question.expert_id = message.from_user.id
        question.expert_answer = custom_answer
        
        # Уменьшаем лимит вопросов у пользователя
        user = session.query(User).get(question.user_id)
        if user and question.status != 'answered':
            user.questions_used += 1
        
        # Сохраняем в архив
        archive = ArchiveEntry(
            question_id=question.id,
            user_id=question.user_id,
            question_text=question.text,
            final_answer=custom_answer,
            topics=[question.topic] if question.topic else []
        )
        session.add(archive)
        session.commit()
        
        # Уведомляем пользователя
        if user:
            try:
                await message.bot.send_message(
                    user.telegram_id,
                    f"✅ <b>Эксперт ответил на ваш вопрос!</b>\n\n"
                    f"📋 ID вопроса: {question_id}\n\n"
                    f"💬 Ответ:\n{custom_answer[:500]}",
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Ошибка отправки пользователю: {e}")
        
        await message.answer(f"✅ Ответ для вопроса #{question_id} отправлен пользователю!")
    
    session.close()
    await state.clear()
    
# bot/handlers.py - добавьте новый обработчик

@router.callback_query(F.data.startswith("supplement_question_"))
async def expert_supplement_question(callback: CallbackQuery, state: FSMContext):
    """Эксперт хочет дополнить ответ ИИ"""
    question_id = callback.data.split("_")[2]
    
    await state.update_data(question_id=question_id)
    
    await callback.message.answer(
        f"✏️ <b>Дополнение к вопросу #{question_id}</b>\n\n"
        f"Введите ваш комментарий или дополнение к ответу ИИ.\n"
        f"Это будет отправлено пользователю как дополнение к существующему ответу:",
        parse_mode="HTML"
    )
    await state.set_state("waiting_for_supplement")
    await callback.answer()


@router.message(F.text, StateFilter("waiting_for_supplement"))
async def process_supplement(message: Message, state: FSMContext):
    """Обработка дополнения от эксперта"""
    data = await state.get_data()
    question_id = data.get('question_id')
    supplement = message.text
    
    session = SessionLocal()
    question = session.query(Question).get(question_id)
    
    if question:
        # Дополняем существующий ответ
        original_answer = question.final_answer or question.rag_answer
        supplemented_answer = f"{original_answer}\n\n---\n\n📝 <b>Дополнение эксперта:</b>\n{supplement}"
        
        question.final_answer = supplemented_answer
        if question.status != 'answered':
            question.status = 'answered'
            question.answered_at = datetime.now()
        
        # Сохраняем в архив
        archive = db.query(ArchiveEntry).filter_by(question_id=question_id).first()
        if archive:
            archive.final_answer = supplemented_answer
        else:
            archive = ArchiveEntry(
                question_id=question.id,
                user_id=question.user_id,
                question_text=question.text,
                final_answer=supplemented_answer,
                topics=[question.topic] if question.topic else []
            )
            session.add(archive)
        
        # Логируем
        from database.models import ExpertLog
        expert_log = ExpertLog(
            expert_id=message.from_user.id,
            question_id=question_id,
            action='supplement',
            new_answer=supplement,
            revision_notes=supplement
        )
        session.add(expert_log)
        
        # Уменьшаем лимит вопросов, если еще не уменьшали
        user = session.query(User).get(question.user_id)
        if user and question.status == 'answered' and not question.expert_id:
            user.questions_used += 1
        
        session.commit()
        
        # Отправляем пользователю дополнение
        if user and user.telegram_id:
            try:
                await message.bot.send_message(
                    user.telegram_id,
                    f"📝 <b>Эксперт дополнил ответ на ваш вопрос!</b>\n\n"
                    f"📋 ID вопроса: {question_id}\n\n"
                    f"💬 <b>Дополнение:</b>\n{supplement}\n\n"
                    f"Полный ответ можно посмотреть в /archive",
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Ошибка отправки: {e}")
        
        await message.answer(f"✅ Дополнение к вопросу #{question_id} отправлено пользователю!")
    
    session.close()
    await state.clear()