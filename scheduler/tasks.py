from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from database.db import SessionLocal
from database.models import Booking, User, ScheduleSlot
import asyncio
import os
from aiogram import Bot

bot = Bot(token=os.getenv("BOT_TOKEN"))
admin_id = int(os.getenv("ADMIN_TELEGRAM_ID"))

def check_upcoming_consultations():
    session = SessionLocal()
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    
    bookings = session.query(Booking).filter(
        Booking.consultation_datetime.between(now, tomorrow),
        Booking.payment_status == 'paid'
    ).all()
    
    for booking in bookings:
        asyncio.create_task(bot.send_message(
            booking.user.telegram_id,
            f"🔔 Напоминание: завтра в {booking.consultation_datetime.strftime('%H:%M')} у вас консультация!"
        ))
        asyncio.create_task(bot.send_message(
            admin_id,
            f"🔔 Напоминание: завтра консультация с {booking.user.name} в {booking.consultation_datetime.strftime('%H:%M')}"
        ))
    
    session.close()

def check_support_expiring():
    session = SessionLocal()
    now = datetime.now()
    two_days_later = now + timedelta(days=2)
    
    bookings = session.query(Booking).filter(
        Booking.support_end_date.between(now, two_days_later),
        Booking.support_end_date.isnot(None)
    ).all()
    
    for booking in bookings:
        asyncio.create_task(bot.send_message(
            admin_id,
            f"⚠️ У {booking.user.name} заканчивается сопровождение через 2 дня!"
        ))
    
    session.close()

def check_unconfirmed_payments():
    session = SessionLocal()
    two_days_ago = datetime.now() - timedelta(days=2)
    
    bookings = session.query(Booking).filter(
        Booking.payment_status == 'waiting_confirm',
        Booking.created_at < two_days_ago
    ).all()
    
    if bookings:
        asyncio.create_task(bot.send_message(
            admin_id,
            f"⚠️ Есть неподтверждённые оплаты: {len(bookings)} шт."
        ))
    
    session.close()

def cleanup_old_slots():
    session = SessionLocal()
    week_ago = datetime.now() - timedelta(days=7)
    session.query(ScheduleSlot).filter(ScheduleSlot.slot_datetime < week_ago).delete()
    session.commit()
    session.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_upcoming_consultations, 'interval', hours=1)
    scheduler.add_job(check_support_expiring, 'interval', days=1)
    scheduler.add_job(check_unconfirmed_payments, 'interval', hours=12)
    scheduler.add_job(cleanup_old_slots, 'interval', weeks=1)
    scheduler.start()