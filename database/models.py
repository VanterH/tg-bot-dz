from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20))
    role = Column(String(20), default='client')
    created_at = Column(DateTime, default=datetime.now)

class Service(Base):
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    price_rub = Column(Integer, nullable=False)
    price_usd = Column(Integer, nullable=False)
    support_days = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    service_id = Column(Integer, ForeignKey('services.id'))
    payment_status = Column(String(50), default='pending')
    payment_currency = Column(String(10), default='RUB')
    payment_proof_url = Column(String(500))
    admin_confirmed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    consultation_datetime = Column(DateTime, nullable=True)
    support_end_date = Column(DateTime, nullable=True)
    is_program_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class ScheduleSlot(Base):
    __tablename__ = 'schedule_slots'
    
    id = Column(Integer, primary_key=True)
    slot_datetime = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, default=False)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

class AdminLog(Base):
    __tablename__ = 'admin_logs'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100))
    target_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)