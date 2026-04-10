# database/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, JSON, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


# ============ СТАРЫЕ МОДЕЛИ (ЗАПИСЬ НА КОНСУЛЬТАЦИИ) ============

class Service(Base):
    """Модель услуги (консультации)"""
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    price_rub = Column(Integer, nullable=False)
    price_usd = Column(Integer, nullable=False)
    support_days = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    bookings = relationship("Booking", back_populates="service")


class ScheduleSlot(Base):
    """Модель временного слота в расписании"""
    __tablename__ = 'schedule_slots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_datetime = Column(DateTime, nullable=False, index=True)
    is_booked = Column(Boolean, default=False, index=True)
    booking_id = Column(Integer, ForeignKey('bookings.id', ondelete='SET NULL'), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Booking(Base):
    """Модель записи на консультацию"""
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='SET NULL'), index=True)
    payment_status = Column(String(50), default='pending', index=True)
    payment_currency = Column(String(10), default='RUB')
    payment_proof_url = Column(String(500), default='')
    admin_confirmed_by = Column(Integer, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    consultation_datetime = Column(DateTime, nullable=True, index=True)
    support_end_date = Column(DateTime, nullable=True)
    is_program_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    user = relationship("User", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    schedule_slot = relationship("ScheduleSlot", back_populates="booking", uselist=False)


ScheduleSlot.booking = relationship("Booking", back_populates="schedule_slot")


# ============ НОВЫЕ МОДЕЛИ (RAG ВОПРОСЫ) ============

class User(Base):
    """Модель пользователя (расширенная)"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    language_code = Column(String(10), default='ru')
    email = Column(String(255))
    phone = Column(String(20))
    
    # Подписка (для RAG)
    subscription_plan = Column(String(50), default='none')
    questions_total = Column(Integer, default=0)
    questions_used = Column(Integer, default=0)
    subscription_valid_until = Column(DateTime)
    subscription_status = Column(String(50), default='pending')
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.now)
    last_active = Column(DateTime, default=datetime.now)
    
    # Связи
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="user", cascade="all, delete-orphan")
    payment_requests = relationship("PaymentRequest", back_populates="user", cascade="all, delete-orphan")


class Question(Base):
    """Модель вопроса пользователя для RAG"""
    __tablename__ = 'questions'
    
    id = Column(String(50), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Текст вопроса
    text = Column(Text, nullable=False)
    topic = Column(String(100))
    age = Column(Integer)
    gender = Column(String(10))
    additional_info = Column(Text)
    
    # Статусы: received, needs_more_info, expert_review, answered, rejected
    status = Column(String(50), default='received', index=True)
    
    # RAG данные
    rag_answer = Column(Text)
    rag_confidence = Column(Float, default=0.0)
    rag_sources = Column(JSON, default=list)
    
    # Экспертная обработка
    expert_id = Column(Integer, nullable=True)
    expert_answer = Column(Text)
    expert_iterations = Column(Integer, default=0)
    expert_revision_notes = Column(Text)
    
    # Финальный ответ
    final_answer = Column(Text)
    answered_at = Column(DateTime)
    
    # Метаданные
    products_used = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    indexed_for_rag = Column(Boolean, default=False)
    
    # Связи
    user = relationship("User", back_populates="questions")


class PaymentRequest(Base):
    """Модель запроса на оплату вопросов"""
    __tablename__ = 'payment_requests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Данные платежа
    plan = Column(String(50), nullable=False)
    amount_rub = Column(Integer)
    amount_usd = Column(Integer)
    questions_count = Column(Integer, default=0)
    valid_days = Column(Integer, default=0)
    
    # Статус
    status = Column(String(50), default='pending', index=True)
    payment_link = Column(String(500))
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.now)
    confirmed_at = Column(DateTime)
    confirmed_by = Column(Integer, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="payment_requests")


class ArchiveEntry(Base):
    """Модель архива вопросов с ответами"""
    __tablename__ = 'archive'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(String(50), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), index=True)
    
    question_text = Column(Text, nullable=False)
    final_answer = Column(Text, nullable=False)
    products_used = Column(JSON, default=list)
    topics = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.now, index=True)


class KnowledgeBase(Base):
    """Модель базы знаний для RAG"""
    __tablename__ = 'knowledge_base'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    kb_id = Column(String(100), unique=True, index=True)
    text = Column(Text, nullable=False)
    
    source = Column(String(500))
    source_type = Column(String(50))
    author = Column(String(255))
    source_url = Column(String(500))
    
    topics = Column(JSON, default=list)
    products = Column(JSON, default=list)
    language = Column(String(10), default='ru')
    
    search_vector = Column(Text)
    chunk_index = Column(Integer, default=0)
    kb_version = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ProductDictionary(Base):
    """Словарь продуктов doTERRA"""
    __tablename__ = 'product_dictionary'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name_en = Column(String(255), unique=True, nullable=False, index=True)
    name_ru = Column(String(255))
    category = Column(String(100))
    restrictions = Column(JSON, default=list)
    description = Column(Text)
    usage = Column(Text)
    is_active = Column(Boolean, default=True)


class ExpertLog(Base):
    """Лог действий эксперта"""
    __tablename__ = 'expert_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    expert_id = Column(Integer, nullable=True)
    question_id = Column(String(50), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    old_answer = Column(Text)
    new_answer = Column(Text)
    revision_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now, index=True)


class SystemSettings(Base):
    """Системные настройки"""
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)