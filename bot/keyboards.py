# bot/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import SessionLocal
from database.models import Service


def main_menu():
    """Главное меню с двумя разделами"""
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Запись на консультацию")],
            [KeyboardButton(text="❓ Задать вопрос эксперту")],
            [KeyboardButton(text="📊 Мой статус"), KeyboardButton(text="📋 Мои записи")],
            [KeyboardButton(text="📋 Архив вопросов"), KeyboardButton(text="💳 Пополнить баланс")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )
    return kb


def services_menu():
    """Клавиатура с услугами"""
    session = SessionLocal()
    services = session.query(Service).filter_by(is_active=True).all()
    session.close()
    
    if not services:
        # Если нет услуг, создаем стандартные
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Премиум - 15000₽", callback_data="service_1")],
            [InlineKeyboardButton(text="Стандарт - 10000₽", callback_data="service_2")],
            [InlineKeyboardButton(text="Базовый - 5000₽", callback_data="service_3")]
        ])
    
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


def slots_list(slots):
    """Клавиатура со списком слотов"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=slot.slot_datetime.strftime("%d.%m %H:%M"), callback_data=f"slot_{slot.id}")]
        for slot in slots[:5]
    ])
    return kb


def slots_button():
    """Кнопка выбора времени"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Выбрать время", callback_data="choose_slot")]
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


def phone_keyboard():
    """Клавиатура для отправки номера телефона"""
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return kb


def get_topics_keyboard():
    """Клавиатура выбора темы вопроса"""
    topics = [
        ("🌿 Иммунитет", "иммунитет"),
        ("😴 Сон", "сон"),
        ("🩺 Кожа", "кожа"),
        ("🍽️ Пищеварение", "пищеварение"),
        ("🧠 Нервная система", "нервная_система"),
        ("💪 Энергия", "энергия"),
        ("❤️ Сердце", "сердце"),
        ("👶 Дети", "дети"),
        ("❓ Другое", "другое")
    ]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=f"topic_{value}")]
        for text, value in topics
    ])
    return kb


def get_payment_keyboard(plan: str, payment_link_rub: str, payment_link_usd: str, payment_id: int):
    """Клавиатура для оплаты вопросов"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить в рублях", url=payment_link_rub)],
        [InlineKeyboardButton(text="💵 Оплатить в долларах", url=payment_link_usd)],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"payment_done_{payment_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])
    return kb