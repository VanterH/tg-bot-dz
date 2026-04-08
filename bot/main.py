import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from bot.handlers import router

load_dotenv()
logging.basicConfig(level=logging.INFO)

# ============ ФУНКЦИЯ ОЧИСТКИ БД ============
def cleanup_database():
    """Полная очистка базы данных при запуске"""
    print("\n" + "="*50)
    print("🧹 ОЧИСТКА БАЗЫ ДАННЫХ")
    print("="*50)
    
    try:
        from database.db import SessionLocal
        from database.models import User, Booking, Service, ScheduleSlot, AdminLog
        
        db = SessionLocal()
        
        # Считаем сколько записей было
        users_count = db.query(User).count()
        bookings_count = db.query(Booking).count()
        
        print(f"📊 Найдено: {users_count} пользователей, {bookings_count} записей")
        
        # Очищаем все таблицы
        db.query(Booking).delete()
        db.query(ScheduleSlot).delete()
        db.query(AdminLog).delete()
        db.query(User).delete()
        
        db.commit()
        
        # Создаем администратора заново
        admin_id = os.getenv('ADMIN_TELEGRAM_ID')
        if admin_id:
            admin = User(
                telegram_id=int(admin_id),
                name='Admin',
                role='admin'
            )
            db.add(admin)
            db.commit()
            print(f"✅ Администратор создан: {admin_id}")
        
        # Проверяем услуги
        if db.query(Service).count() == 0:
            services = [
                Service(name='Премиум', price_rub=15000, price_usd=200, support_days=30),
                Service(name='Стандарт', price_rub=10000, price_usd=130, support_days=30),
                Service(name='Базовый', price_rub=5000, price_usd=70, support_days=0)
            ]
            for s in services:
                db.add(s)
            db.commit()
            print("✅ Услуги созданы")
        
        db.close()
        
        print("✅ БАЗА ДАННЫХ ОЧИЩЕНА!")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")

# ============ ИНИЦИАЛИЗАЦИЯ ============
def init_database():
    from database.db import init_db
    init_db()

# ============ ЗАПУСК ============
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(storage=MemoryStorage())

async def main():
    print("\n🚀 ЗАПУСК БОТА...")
    #cleanup_database()
    init_database()      # Создаем таблицы
    cleanup_database()   # Очищаем данные
    dp.include_router(router)
    print("🤖 Бот запущен! Нажмите Ctrl+C для остановки\n")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")