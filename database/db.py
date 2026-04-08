import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, User, Service

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:toor@localhost:5432/booking_bot')

# Для SQLite
if 'sqlite' in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    try:
        # Создаем админа если нет
        admin_id = os.getenv('ADMIN_TELEGRAM_ID')
        if admin_id:
            admin = session.query(User).filter_by(telegram_id=int(admin_id)).first()
            if not admin:
                admin = User(
                    telegram_id=int(admin_id),
                    name='Admin',
                    role='admin'
                )
                session.add(admin)
                session.commit()
                print(f"✅ Админ создан с ID: {admin_id}")
        
        # Создаем услуги если нет
        if session.query(Service).count() == 0:
            services = [
                Service(name='Премиум', price_rub=15000, price_usd=200, support_days=30, is_active=True),
                Service(name='Стандарт', price_rub=10000, price_usd=130, support_days=30, is_active=True),
                Service(name='Базовый', price_rub=5000, price_usd=70, support_days=0, is_active=True)
            ]
            for service in services:
                session.add(service)
            session.commit()
            print("✅ Услуги созданы")
        
        print("✅ База данных успешно инициализирована")
    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        session.rollback()
    finally:
        session.close()
        
        
def get_db():
    """Генератор сессии базы данных для FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()