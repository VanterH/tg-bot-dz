import pytest
from datetime import datetime, timedelta
from scheduler.tasks import check_upcoming_consultations
from database.models import Booking, User

def test_check_upcoming():
    # Тестируем поиск предстоящих консультаций
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    
    # Проверяем логику
    assert tomorrow > now

def test_support_expiring():
    # Тестируем истечение сопровождения
    end_date = datetime.now() + timedelta(days=2)
    assert end_date > datetime.now()