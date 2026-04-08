import pytest
from database.models import User, Service, Booking
from datetime import datetime

def test_create_user():
    user = User(telegram_id=123456, name="Test User", role="client")
    assert user.telegram_id == 123456
    assert user.name == "Test User"

def test_create_booking():
    booking = Booking(payment_status='pending')
    assert booking.payment_status == 'pending'

def test_service_price():
    service = Service(name="Test", price_rub=5000, price_usd=70)
    assert service.price_rub == 5000
    assert service.price_usd == 70