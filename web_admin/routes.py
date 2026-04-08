"""
Дополнительные маршруты для админ-панели
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import User, Booking, Service, ScheduleSlot, AdminLog
from datetime import datetime, timedelta
import pandas as pd
import os
import json

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_admin(request: Request):
    """Проверка авторизации администратора"""
    token = request.cookies.get("admin_token")
    if not token or token != os.getenv("SECRET_KEY", "admin123"):
        return False
    return True

@router.get("/logout")
async def logout():
    """Выход из админ-панели"""
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("admin_token")
    return response

@router.get("/export/csv")
async def export_csv(request: Request, db: Session = Depends(get_db)):
    """Экспорт данных в CSV"""
    if not verify_admin(request):
        return RedirectResponse("/login", status_code=303)
    
    bookings = db.query(Booking).all()
    data = []
    for b in bookings:
        data.append({
            "ID": b.id,
            "Клиент": b.user.name if b.user else "",
            "Telegram ID": b.user.telegram_id if b.user else "",
            "Услуга": b.service.name if b.service else "",
            "Цена (RUB)": b.service.price_rub if b.service else 0,
            "Статус оплаты": b.payment_status,
            "Дата консультации": b.consultation_datetime.strftime("%Y-%m-%d %H:%M") if b.consultation_datetime else "",
            "Дата создания": b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "",
            "Программа отправлена": "Да" if b.is_program_sent else "Нет"
        })
    
    df = pd.DataFrame(data)
    csv_file = "report.csv"
    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    
    return FileResponse(csv_file, filename=f"report_{datetime.now().strftime('%Y%m%d')}.csv")

@router.post("/update_service/{service_id}")
async def update_service(
    request: Request, 
    service_id: int, 
    price_rub: int = None,
    price_usd: int = None,
    db: Session = Depends(get_db)
):
    """Обновление цены услуги"""
    if not verify_admin(request):
        return RedirectResponse("/login", status_code=303)
    
    service = db.query(Service).get(service_id)
    if service:
        form_data = await request.form()
        if price_rub:
            service.price_rub = price_rub
        elif "price_rub" in form_data:
            service.price_rub = int(form_data["price_rub"])
        if price_usd:
            service.price_usd = price_usd
        db.commit()
        
        # Логируем действие
        log = AdminLog(
            admin_id=1,
            action=f"update_service_price_{service_id}",
            target_id=service_id
        )
        db.add(log)
        db.commit()
    
    return RedirectResponse("/settings", status_code=303)

@router.post("/update_payment_details")
async def update_payment_details(request: Request, db: Session = Depends(get_db)):
    """Обновление реквизитов для оплаты"""
    if not verify_admin(request):
        return RedirectResponse("/login", status_code=303)
    
    form_data = await request.form()
    payment_details = form_data.get("payment_details", "")
    
    # Сохраняем в файл или в БД
    with open("payment_details.txt", "w", encoding="utf-8") as f:
        f.write(payment_details)
    
    return RedirectResponse("/settings", status_code=303)

@router.get("/booking/{booking_id}")
async def get_booking_details(request: Request, booking_id: int, db: Session = Depends(get_db)):
    """Детали конкретной заявки"""
    if not verify_admin(request):
        return {"error": "Unauthorized"}
    
    booking = db.query(Booking).get(booking_id)
    if not booking:
        return {"error": "Booking not found"}
    
    return {
        "id": booking.id,
        "client_name": booking.user.name if booking.user else "",
        "client_phone": booking.user.phone if booking.user else "",
        "service": booking.service.name if booking.service else "",
        "price": booking.service.price_rub if booking.service else 0,
        "status": booking.payment_status,
        "consultation_date": booking.consultation_datetime.strftime("%Y-%m-%d %H:%M") if booking.consultation_datetime else "",
        "program_sent": booking.is_program_sent,
        "support_end": booking.support_end_date.strftime("%Y-%m-%d") if booking.support_end_date else ""
    }

@router.post("/mark_program_sent/{booking_id}")
async def mark_program_sent(request: Request, booking_id: int, db: Session = Depends(get_db)):
    """Отметить что программа отправлена клиенту"""
    if not verify_admin(request):
        return RedirectResponse("/login", status_code=303)
    
    booking = db.query(Booking).get(booking_id)
    if booking:
        booking.is_program_sent = True
        db.commit()
    
    return RedirectResponse(f"/bookings", status_code=303)

@router.get("/api/stats")
async def get_stats(request: Request, db: Session = Depends(get_db)):
    """API для получения статистики (AJAX)"""
    if not verify_admin(request):
        return {"error": "Unauthorized"}
    
    total_clients = db.query(User).filter_by(role='client').count()
    active_support = db.query(Booking).filter(
        Booking.support_end_date > datetime.now(),
        Booking.payment_status == 'paid'
    ).count()
    
    month_income = db.query(Booking).filter(
        Booking.payment_status == 'paid',
        Booking.confirmed_at > datetime.now() - timedelta(days=30)
    ).all()
    total_income = sum(b.service.price_rub if b.service else 0 for b in month_income)
    
    # Статистика по услугам
    service_stats = []
    services = db.query(Service).all()
    for service in services:
        count = db.query(Booking).filter_by(service_id=service.id, payment_status='paid').count()
        service_stats.append({
            "name": service.name,
            "count": count,
            "revenue": count * service.price_rub
        })
    
    return {
        "total_clients": total_clients,
        "active_support": active_support,
        "month_income": total_income,
        "service_stats": service_stats
    }