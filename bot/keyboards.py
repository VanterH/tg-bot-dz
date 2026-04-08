# bot/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import SessionLocal
from database.models import Service

def main_menu():
    """Главное меню бота"""
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записаться")],
            [KeyboardButton(text="ℹ️ Мои записи")]
        ],
        resize_keyboard=True
    )
    return kb

def phone_keyboard():
    """Клавиатура для запроса номера телефона"""
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return kb

def services_menu():
    """Клавиатура с услугами"""
    session = SessionLocal()
    services = session.query(Service).filter_by(is_active=True).all()
    session.close()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{s.name} - {s.price_rub}₽", callback_data=f"service_{s.id}")]
        for s in services
    ])
    return kb

def payment_button():
    """Кнопка 'Я оплатил'"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Я оплатил(а)", callback_data="payment_made")]
    ])
    return kb

def slots_button():
    """Кнопка для выбора времени"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Выбрать время", callback_data="choose_slot")]
    ])
    return kb

def slots_list(slots):
    """Клавиатура со списком доступных слотов"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=slot.slot_datetime.strftime("%d.%m %H:%M"), callback_data=f"slot_{slot.id}")]
        for slot in slots[:5]  # Показываем максимум 5 слотов
    ])
    return kb

def back_button():
    """Кнопка назад"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])
    return kb

def cancel_button():
    """Кнопка отмены"""
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return kb