from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import Response
from database.db import SessionLocal
from database.models import User, Booking, Service, ScheduleSlot
from datetime import datetime, timedelta
import os
import csv
from io import StringIO

app = FastAPI(title="Admin Panel")
templates = Jinja2Templates(directory="web_admin/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

ADMIN_TOKEN = os.getenv("SECRET_KEY", "admin123")

def verify_token(request: Request):
    token = request.cookies.get("admin_token")
    return token == ADMIN_TOKEN

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    if password == ADMIN_TOKEN:
        response = RedirectResponse("/", status_code=303)
        response.set_cookie("admin_token", ADMIN_TOKEN)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Wrong password"})

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
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
    
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).limit(10).all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_clients": total_clients,
        "active_support": active_support,
        "month_income": total_income,
        "bookings": bookings
    })

@app.get("/bookings", response_class=HTMLResponse)
async def bookings_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
    return templates.TemplateResponse("bookings.html", {
        "request": request,
        "bookings": bookings
    })

@app.post("/confirm_booking/{booking_id}")
async def confirm_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).get(booking_id)
    if booking:
        booking.payment_status = 'paid'
        booking.confirmed_at = datetime.now()
        db.commit()
    return RedirectResponse("/bookings", status_code=303)

@app.get("/schedule", response_class=HTMLResponse)
async def schedule_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    slots = db.query(ScheduleSlot).order_by(ScheduleSlot.slot_datetime).all()
    return templates.TemplateResponse("schedule.html", {
        "request": request,
        "slots": slots
    })

@app.get("/clients", response_class=HTMLResponse)
async def clients_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    clients = db.query(User).filter_by(role='client').all()
    return templates.TemplateResponse("clients.html", {
        "request": request,
        "clients": clients
    })

@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    total_consultations = db.query(Booking).filter(Booking.payment_status == 'paid').count()
    total_bookings = db.query(Booking).count()
    conversion_rate = round((total_consultations / total_bookings * 100) if total_bookings > 0 else 0)
    
    return templates.TemplateResponse("reports.html", {
        "request": request,
        "total_consultations": total_consultations,
        "conversion_rate": conversion_rate,
        "months": [],
        "incomes": []
    })

@app.get("/export/csv")
async def export_csv(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    bookings = db.query(Booking).all()
    
    # Создаем CSV вручную
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Клиент', 'Услуга', 'Статус', 'Сумма', 'Дата'])
    
    for b in bookings:
        writer.writerow([
            b.id,
            b.user.name if b.user else '',
            b.service.name if b.service else '',
            b.payment_status,
            b.service.price_rub if b.service else 0,
            b.created_at.strftime('%Y-%m-%d') if b.created_at else ''
        ])
    
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=report_{datetime.now().strftime('%Y%m%d')}.csv"
    return response

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    services = db.query(Service).all()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "services": services
    })

@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("admin_token")
    return response