# bot/handlers.py
import os
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from datetime import datetime
from database.db import SessionLocal
from database.models import User, Booking, Service, ScheduleSlot
from bot.keyboards import main_menu, phone_keyboard, services_menu, payment_button, slots_button, slots_list, cancel_button
from bot.utils import send_admin_notification

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

# ============ КОМАНДА /start ============
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    await state.clear()
    
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        user = User(
            telegram_id=message.from_user.id,
            name=message.from_user.full_name,
            role='client'
        )
        session.add(user)
        session.commit()
        await message.answer(
            "👋 Добро пожаловать!\n\n"
            "Я помогу вам записаться на консультацию.\n"
            "Как вас называть?",
            reply_markup=cancel_button()
        )
        await state.set_state(BookingStates.waiting_for_name)
    else:
        await message.answer(
            f"👋 С возвращением, {user.name}!\n\n"
            "Выберите действие:",
            reply_markup=main_menu()
        )
    
    session.close()

# ============ ОБРАБОТКА ОТМЕНЫ ============
@router.message(F.text == "❌ Отмена")
async def cancel_operation(message: Message, state: FSMContext):
    """Отмена текущей операции"""
    await state.clear()
    await message.answer(
        "✅ Операция отменена.\n"
        "Используйте /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Команда /cancel"""
    await state.clear()
    await message.answer(
        "✅ Операция отменена.\n"
        "Используйте /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )

# ============ ПОЛУЧЕНИЕ ИМЕНИ ============
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

# ============ ПОЛУЧЕНИЕ ТЕЛЕФОНА ============
@router.message(BookingStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    """Получение номера телефона"""
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text
    
    data = await state.get_data()
    name = data.get('name')
    
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    if user:
        user.name = name
        user.phone = phone
        session.commit()
    
    session.close()
    
    await state.update_data(phone=phone)
    await message.answer(
        "Выберите услугу:",
        reply_markup=services_menu()
    )
    await state.set_state(BookingStates.waiting_for_service)

# ============ ВЫБОР УСЛУГИ ============
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
    
    await state.update_data(service_id=service_id, service_price=service.price_rub)
    
    await callback.message.edit_text(
        f"✅ Выбрано: {service.name}\n"
        f"💰 Цена: {service.price_rub}₽\n\n"
        f"После оплаты нажмите кнопку ниже и отправьте скриншот чека:",
        reply_markup=payment_button()
    )
    await state.set_state(BookingStates.waiting_for_payment)
    session.close()
    await callback.answer()

# ============ ОПЛАТА ============
@router.callback_query(F.data == "payment_made", BookingStates.waiting_for_payment)
async def payment_made(callback: CallbackQuery, state: FSMContext):
    """Пользователь нажал 'Я оплатил'"""
    await callback.message.answer(
        "📸 Пожалуйста, отправьте скриншот чека об оплате:",
        reply_markup=cancel_button()
    )
    await state.update_data(waiting_for_screenshot=True)
    await callback.answer()

# ============ ПОЛУЧЕНИЕ СКРИНШОТА ============
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
        "После подтверждения администратором вы сможете выбрать время.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Уведомляем администратора
    await send_admin_notification(message.bot, booking_id, data['service_price'])
    await state.clear()

# ============ КНОПКА "ЗАПИСАТЬСЯ" ============
@router.message(F.text == "📅 Записаться")
async def book_appointment(message: Message, state: FSMContext):
    """Начало записи"""
    await state.clear()
    
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    if not user or not user.phone:
        await message.answer(
            "Давайте начнем регистрацию!\n\n"
            "Как вас называть?",
            reply_markup=cancel_button()
        )
        await state.set_state(BookingStates.waiting_for_name)
    else:
        await message.answer(
            f"👋 {user.name}, выберите услугу:",
            reply_markup=services_menu()
        )
        await state.set_state(BookingStates.waiting_for_service)
    
    session.close()

# ============ КНОПКА "МОИ ЗАПИСИ" ============
@router.message(F.text == "ℹ️ Мои записи")
async def my_bookings(message: Message):
    """Просмотр своих записей"""
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("❌ Пользователь не найден. Отправьте /start")
        session.close()
        return
    
    bookings = session.query(Booking).filter_by(user_id=user.id).order_by(Booking.created_at.desc()).all()
    
    if not bookings:
        await message.answer("📭 У вас пока нет записей.\nНажмите «Записаться» чтобы создать новую.")
    else:
        text = "📋 <b>Ваши записи:</b>\n\n"
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

# ============ ВЫБОР ВРЕМЕНИ ============
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
        
        # Получаем свободные слоты
        slots = session.query(ScheduleSlot).filter(
            ScheduleSlot.slot_datetime > datetime.now(),
            ScheduleSlot.is_booked == False
        ).limit(10).all()
        
        if not slots:
            await callback.message.answer("❌ Нет доступных слотов для записи. Загляните позже!")
            await callback.answer()
            return
        
        await callback.message.edit_text(
            "🗓️ <b>Доступное время для записи:</b>\n\n"
            "Выберите удобное время:",
            reply_markup=slots_list(slots),
            parse_mode="HTML"
        )
    finally:
        session.close()
    
    await callback.answer()

# ============ БРОНИРОВАНИЕ СЛОТА ============
@router.callback_query(F.data.startswith("slot_"))
async def book_slot_callback(callback: CallbackQuery):
    """Обработка выбора слота"""
    slot_id = int(callback.data.split("_")[1])
    
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
        
        # Бронируем слот
        slot.is_booked = True
        slot.booking_id = booking.id
        booking.consultation_datetime = slot.slot_datetime
        session.commit()
        
        await callback.message.edit_text(
            f"✅ <b>Время успешно забронировано!</b>\n\n"
            f"📅 Дата и время: {slot.slot_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Вы получите напоминание за 24 часа до консультации.\n\n"
            f"Вернуться в главное меню: /start",
            parse_mode="HTML"
        )
    finally:
        session.close()
    
    await callback.answer()

# ============ КНОПКА НАЗАД ============
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await callback.message.edit_text("Выберите действие:", reply_markup=None)
    await callback.message.answer("Главное меню:", reply_markup=main_menu())
    await callback.answer()