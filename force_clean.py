# force_cleanup.py - принудительная очистка БД
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("ПРИНУДИТЕЛЬНАЯ ОЧИСТКА БАЗЫ ДАННЫХ")
print("="*60)

from database.db import SessionLocal, engine
from database.models import Base

db = SessionLocal()

# Полная пересоздание всех таблиц
print("\n🗑️ Удаляем все таблицы...")
Base.metadata.drop_all(bind=engine)
print("✅ Таблицы удалены")

print("\n🔄 Создаем таблицы заново...")
Base.metadata.create_all(bind=engine)
print("✅ Таблицы созданы")

# Создаем администратора
from database.models import User, Service

admin_id = os.getenv('ADMIN_TELEGRAM_ID')
if admin_id:
    admin = User(telegram_id=int(admin_id), name='Admin', role='admin')
    db.add(admin)
    print(f"✅ Администратор создан: {admin_id}")

# Создаем услуги
services = [
    Service(name='Премиум', price_rub=15000, price_usd=200, support_days=30, is_active=True),
    Service(name='Стандарт', price_rub=10000, price_usd=130, support_days=30, is_active=True),
    Service(name='Базовый', price_rub=5000, price_usd=70, support_days=0, is_active=True)
]
for s in services:
    db.add(s)
db.commit()
print("✅ Услуги созданы")

db.close()

print("\n✅ БАЗА ДАННЫХ ПОЛНОСТЬЮ ОЧИЩЕНА И ПЕРЕСОЗДАНА!")
