# Экспортируем все модели для удобного импорта
from models.base import Base
from models.user import User
from models.service import Service
from models.booking import Booking
from models.schedule_slot import ScheduleSlot
from models.admin_log import AdminLog

# Список всех моделей для создания таблиц
__all__ = [
    "Base",
    "User",
    "Service",
    "Booking",
    "ScheduleSlot",
    "AdminLog"
]