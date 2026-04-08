"""
Telegram Bot Package
Содержит основную логику Telegram бота для записи на консультации
"""

from bot.handlers import router
from bot.keyboards import main_menu, services_menu
from bot.states import BookingStates

__all__ = ['router', 'main_menu', 'services_menu', 'BookingStates']