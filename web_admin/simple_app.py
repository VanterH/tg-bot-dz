import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uvicorn
from aiogram import Bot
from database.db import SessionLocal, get_db
from database.models import User, Booking, Service, ScheduleSlot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None

app = FastAPI()
ADMIN_PASSWORD = "admin123"

# Базовый HTML шаблон со стилями
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; background: #f5f5f5; }}
        .sidebar {{
            width: 250px;
            background: #2c3e50;
            color: white;
            position: fixed;
            height: 100%;
            padding: 20px;
            top: 0;
            left: 0;
        }}
        .sidebar h2 {{ margin-bottom: 30px; font-size: 20px; }}
        .sidebar a {{
            color: white;
            text-decoration: none;
            display: block;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            transition: background 0.3s;
        }}
        .sidebar a:hover {{ background: #34495e; }}
        .content {{
            margin-left: 250px;
            padding: 30px;
        }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{ color: #7f8c8d; margin-top: 10px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: bold;
        }}
        tr:hover {{ background: #f5f5f5; }}
        .btn {{
            padding: 8px 15px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
            display: inline-block;
            margin: 2px;
        }}
        .btn-success {{ background: #27ae60; color: white; }}
        .btn-danger {{ background: #e74c3c; color: white; }}
        .btn-primary {{ background: #3498db; color: white; }}
        .btn-warning {{ background: #f39c12; color: white; }}
        .status {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .status-paid {{ background: #27ae60; color: white; }}
        .status-waiting_confirm {{ background: #f39c12; color: white; }}
        .status-pending {{ background: #95a5a6; color: white; }}
        .status-rejected {{ background: #e74c3c; color: white; }}
        h1 {{ margin-bottom: 20px; color: #333; }}
        .form-group {{ margin-bottom: 15px; }}
        .form-group label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
        .form-group input, .form-group select {{ padding: 8px; width: 100%; max-width: 300px; }}
        .slot-free {{ color: green; }}
        .slot-booked {{ color: red; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>📊 Admin Panel</h2>
        <a href="/">📈 Дашборд</a>
        <a href="/bookings">📋 Заявки</a>
        <a href="/schedule">📅 Расписание</a>
        <a href="/clients">👥 Клиенты</a>
        <a href="/reports">📊 Отчёты</a>
        <a href="/settings">⚙️ Настройки</a>
        <a href="/logout">🚪 Выход</a>
    </div>
    <div class="content">
        {content}
    </div>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Вход в админ-панель</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
        }}
        .login-box {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            width: 350px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }}
        h2 {{ text-align: center; margin-bottom: 30px; color: #333; }}
        input {{ width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }}
        button {{ width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }}
        button:hover {{ background: #5a67d8; }}
        .error {{ color: red; text-align: center; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🔐 Вход в админ-панель</h2>
        <form method="post">
            <input type="password" name="password" placeholder="Введите пароль" required>
            <button type="submit">Войти</button>
        </form>
        {error}
    </div>
</body>
</html>
"""

def render_page(title: str, content: str) -> str:
    return BASE_HTML.format(title=title, content=content)

def verify_token(request: Request):
    token = request.cookies.get("admin_token")
    return token == ADMIN_PASSWORD

# ============ ПРОСМОТР ФОТО ЧЕКА ============
@app.get("/receipt/{booking_id}")
async def view_receipt(booking_id: int, request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    booking = db.query(Booking).get(booking_id)
    if not booking or not booking.payment_proof_url:
        return HTMLResponse("<h3>❌ Фото чека не найдено</h3>", status_code=404)
    
    if os.path.exists(booking.payment_proof_url):
        return FileResponse(booking.payment_proof_url, media_type="image/jpeg")
    return HTMLResponse("<h3>❌ Файл не найден</h3>", status_code=404)

# ============ ДАШБОРД ============
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
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
    total_income = 0
    for b in month_income:
        service = db.query(Service).get(b.service_id)
        if service:
            total_income += service.price_rub
    
    recent_bookings = db.query(Booking).order_by(Booking.created_at.desc()).limit(5).all()
    bookings_html = ""
    for b in recent_bookings:
        user = db.query(User).get(b.user_id)
        service = db.query(Service).get(b.service_id)
        bookings_html += f"""
        <tr>
            <td>{b.id}</td>
            <td>{user.name if user else '-'}</td>
            <td>{service.name if service else '-'}</td>
            <td><span class="status status-{b.payment_status}">{b.payment_status}</span></td>
            <td>{b.created_at.strftime('%d.%m.%Y %H:%M') if b.created_at else '-'}</td>
        </tr>
        """
    
    if not recent_bookings:
        bookings_html = '<tr><td colspan="5" style="text-align: center; color: #999;">Нет заявок</td></tr>'
    
    content = f"""
    <h1>📈 Дашборд</h1>
    <div class="stats">
        <div class="stat-card"><div class="stat-number">{total_clients}</div><div class="stat-label">Всего клиентов</div></div>
        <div class="stat-card"><div class="stat-number">{active_support}</div><div class="stat-label">Активных сопровождений</div></div>
        <div class="stat-card"><div class="stat-number">{total_income}₽</div><div class="stat-label">Доход за месяц</div></div>
    </div>
    <div class="card">
        <h3>Последние заявки</h3>
        <table><thead><tr><th>ID</th><th>Клиент</th><th>Услуга</th><th>Статус</th><th>Дата</th></tr></thead>
        <tbody>{bookings_html}</tbody></table>
    </div>
    """
    return render_page("Дашборд", content)

# ============ ЛОГИН ============
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return LOGIN_HTML.format(error="")

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        response = RedirectResponse("/", status_code=303)
        response.set_cookie("admin_token", ADMIN_PASSWORD)
        return response
    return LOGIN_HTML.format(error='<div class="error">❌ Неверный пароль!</div>')

# ============ ЗАЯВКИ ============
@app.get("/bookings", response_class=HTMLResponse)
async def bookings_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
    table_html = ""
    for b in bookings:
        user = db.query(User).get(b.user_id)
        service = db.query(Service).get(b.service_id)
        
        receipt_link = ""
        if b.payment_proof_url and os.path.exists(b.payment_proof_url):
            receipt_link = f'<a href="/receipt/{b.id}" target="_blank" class="btn btn-primary">📷 Чек</a>'
        else:
            receipt_link = '<span style="color: #999;">Нет чека</span>'
        
        if b.payment_status == 'waiting_confirm':
            action_buttons = f'''
                <form method="post" action="/confirm/{b.id}" style="display:inline">
                    <button type="submit" class="btn btn-success">✅ Подтвердить</button>
                </form>
                <form method="post" action="/reject/{b.id}" style="display:inline">
                    <button type="submit" class="btn btn-danger">❌ Отклонить</button>
                </form>
            '''
        else:
            action_buttons = '<span style="color: #999;">Нет действий</span>'
        
        table_html += f"""
        <tr>
            <td>{b.id}</td>
            <td>{user.name if user else '-'}</td>
            <td>{service.name if service else '-'}</td>
            <td>{service.price_rub if service else 0}₽</td>
            <td><span class="status status-{b.payment_status}">{b.payment_status}</span></td>
            <td>{b.created_at.strftime('%d.%m.%Y %H:%M') if b.created_at else '-'}</td>
            <td>{receipt_link}</td>
            <td>{action_buttons}</td>
        </tr>
        """
    
    if not bookings:
        table_html = '<tr><td colspan="8" style="text-align: center;">Нет заявок</td></tr>'
    
    content = f"""
    <h1>📋 Управление заявками</h1>
    <div class="card">
        <table>
            <thead><tr><th>ID</th><th>Клиент</th><th>Услуга</th><th>Сумма</th><th>Статус</th><th>Дата</th><th>Чек</th><th>Действие</th></tr></thead>
            <tbody>{table_html}</tbody>
        </table>
    </div>
    """
    return render_page("Заявки", content)

@app.post("/confirm/{booking_id}")
async def confirm_booking(booking_id: int, request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    booking = db.query(Booking).get(booking_id)
    if booking:
        booking.payment_status = 'paid'
        booking.confirmed_at = datetime.now()
        db.commit()
        
        user = db.query(User).get(booking.user_id)
        service = db.query(Service).get(booking.service_id)
        
        if bot and user and user.telegram_id:
            try:
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📅 Выбрать время", callback_data="choose_slot")]
                ])
                await bot.send_message(
                    user.telegram_id,
                    f"✅ <b>Оплата подтверждена!</b>\n\n"
                    f"📋 Услуга: {service.name if service else '-'}\n"
                    f"💰 Сумма: {service.price_rub if service else 0}₽\n\n"
                    f"Теперь вы можете выбрать время для консультации.",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Ошибка: {e}")
    
    return RedirectResponse("/bookings", status_code=303)

@app.post("/reject/{booking_id}")
async def reject_booking(booking_id: int, request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    booking = db.query(Booking).get(booking_id)
    if booking:
        booking.payment_status = 'rejected'
        db.commit()
        
        user = db.query(User).get(booking.user_id)
        if bot and user and user.telegram_id:
            try:
                await bot.send_message(user.telegram_id, f"❌ Ваша оплата отклонена.")
            except Exception as e:
                print(f"Ошибка: {e}")
    
    return RedirectResponse("/bookings", status_code=303)

# ============ УПРАВЛЕНИЕ РАСПИСАНИЕМ ============
@app.get("/schedule", response_class=HTMLResponse)
async def schedule_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    slots = db.query(ScheduleSlot).order_by(ScheduleSlot.slot_datetime).all()
    
    slots_html = ""
    for slot in slots:
        client_name = '-'
        if slot.is_booked and slot.booking_id:
            booking = db.query(Booking).get(slot.booking_id)
            if booking:
                user = db.query(User).get(booking.user_id)
                if user:
                    client_name = user.name
        
        status_class = "slot-free" if not slot.is_booked else "slot-booked"
        status_text = "🟢 Свободен" if not slot.is_booked else "🔴 Занят"
        
        slots_html += f"""
        <tr>
            <td>{slot.id}</td>
            <td>{slot.slot_datetime.strftime('%d.%m.%Y %H:%M') if slot.slot_datetime else '-'}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{client_name}</td>
            <td>
                <form method="post" action="/delete_slot/{slot.id}" style="display:inline" 
                      onsubmit="return confirm('Удалить слот?')">
                    <button type="submit" class="btn btn-danger">🗑️ Удалить</button>
                </form>
            </td>
        </tr>
        """
    
    if not slots:
        slots_html = '<tr><td colspan="5" style="text-align: center;">Нет слотов</td></tr>'
    
    content = f"""
    <h1>📅 Управление расписанием</h1>
    
    <div class="card">
        <h3>➕ Добавить новый слот</h3>
        <form method="post" action="/add_slot">
            <div class="form-group">
                <label>Дата:</label>
                <input type="date" name="date" required>
            </div>
            <div class="form-group">
                <label>Время начала:</label>
                <input type="time" name="time" required>
            </div>
            <div class="form-group">
                <label>Длительность (минуты):</label>
                <select name="duration">
                    <option value="30">30 минут</option>
                    <option value="60">1 час</option>
                    <option value="90">1.5 часа</option>
                    <option value="120">2 часа</option>
                </select>
            </div>
            <button type="submit" class="btn btn-primary">➕ Добавить слот</button>
        </form>
    </div>
    
    <div class="card">
        <h3>📅 Создать слоты на неделю</h3>
        <form method="post" action="/add_week_slots">
            <div class="form-group">
                <label>Начальная дата:</label>
                <input type="date" name="start_date" required>
            </div>
            <div class="form-group">
                <label>Время начала (по умолчанию 10:00):</label>
                <input type="time" name="start_time" value="10:00">
            </div>
            <div class="form-group">
                <label>Время окончания (по умолчанию 18:00):</label>
                <input type="time" name="end_time" value="18:00">
            </div>
            <div class="form-group">
                <label>Интервал (минуты):</label>
                <select name="interval">
                    <option value="60">Каждый час</option>
                    <option value="120">Каждые 2 часа</option>
                    <option value="30">Каждые 30 минут</option>
                </select>
            </div>
            <div class="form-group">
                <label>Длительность слота (минуты):</label>
                <select name="duration">
                    <option value="60">1 час</option>
                    <option value="30">30 минут</option>
                    <option value="90">1.5 часа</option>
                </select>
            </div>
            <button type="submit" class="btn btn-success">📅 Создать слоты на неделю</button>
        </form>
    </div>
    
    <div class="card">
        <h3>📋 Текущие слоты</h3>
        <table>
            <thead>
                <tr><th>ID</th><th>Дата и время</th><th>Статус</th><th>Клиент</th><th>Действие</th></tr>
            </thead>
            <tbody>{slots_html}</tbody>
        </table>
    </div>
    """
    return render_page("Расписание", content)

@app.post("/add_slot")
async def add_slot(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    form = await request.form()
    date_str = form.get('date')
    time_str = form.get('time')
    duration = int(form.get('duration', 60))
    
    try:
        slot_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        # Проверяем не существует ли уже такой слот
        existing = db.query(ScheduleSlot).filter_by(slot_datetime=slot_datetime).first()
        if existing:
            return HTMLResponse("<h3>❌ Слот на это время уже существует!</h3><a href='/schedule'>Назад</a>", status_code=400)
        
        slot = ScheduleSlot(
            slot_datetime=slot_datetime,
            is_booked=False
        )
        db.add(slot)
        db.commit()
        
        # Если длительность больше часа, создаем дополнительный слот
        if duration > 60:
            extra_time = slot_datetime + timedelta(minutes=duration)
            # Проверяем что такой слот еще не существует
            extra_existing = db.query(ScheduleSlot).filter_by(slot_datetime=extra_time).first()
            if not extra_existing:
                extra_slot = ScheduleSlot(
                    slot_datetime=extra_time,
                    is_booked=False
                )
                db.add(extra_slot)
                db.commit()
        
    except Exception as e:
        return HTMLResponse(f"<h3>❌ Ошибка: {e}</h3><a href='/schedule'>Назад</a>", status_code=400)
    
    return RedirectResponse("/schedule", status_code=303)

@app.post("/add_week_slots")
async def add_week_slots(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    form = await request.form()
    start_date_str = form.get('start_date')
    start_time_str = form.get('start_time', '10:00')
    end_time_str = form.get('end_time', '18:00')
    interval = int(form.get('interval', 60))
    duration = int(form.get('duration', 60))
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        start_time = datetime.strptime(start_time_str, "%H:%M").time()
        end_time = datetime.strptime(end_time_str, "%H:%M").time()
        
        slots_created = 0
        
        # Создаем слоты на 7 дней
        for day in range(7):
            current_date = start_date + timedelta(days=day)
            
            # Создаем время начала
            current_hour = start_time.hour
            current_minute = start_time.minute
            
            while True:
                slot_time = datetime(
                    current_date.year, current_date.month, current_date.day,
                    current_hour, current_minute
                )
                
                # Проверяем не вышли ли за пределы
                if slot_time.time() > end_time:
                    break
                
                # Проверяем не существует ли уже такой слот
                existing = db.query(ScheduleSlot).filter_by(slot_datetime=slot_time).first()
                if not existing and slot_time > datetime.now():
                    slot = ScheduleSlot(
                        slot_datetime=slot_time,
                        is_booked=False
                    )
                    db.add(slot)
                    slots_created += 1
                
                # Увеличиваем время на интервал
                current_minute += interval
                if current_minute >= 60:
                    current_hour += current_minute // 60
                    current_minute = current_minute % 60
        
        db.commit()
        
        return HTMLResponse(f"""
        <h3>✅ Создано {slots_created} слотов на неделю!</h3>
        <a href="/schedule">Вернуться к расписанию</a>
        """)
        
    except Exception as e:
        return HTMLResponse(f"<h3>❌ Ошибка: {e}</h3><a href='/schedule'>Назад</a>", status_code=400)

@app.post("/delete_slot/{slot_id}")
async def delete_slot(slot_id: int, request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    slot = db.query(ScheduleSlot).get(slot_id)
    if slot:
        db.delete(slot)
        db.commit()
    
    return RedirectResponse("/schedule", status_code=303)

# ============ КЛИЕНТЫ ============
@app.get("/clients", response_class=HTMLResponse)
async def clients_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    clients = db.query(User).filter_by(role='client').all()
    clients_html = ""
    for client in clients:
        bookings_count = db.query(Booking).filter_by(user_id=client.id).count()
        clients_html += f"""
        <tr>
            <td>{client.id}</td>
            <td>{client.telegram_id}</td>
            <td>{client.name}</td>
            <td>{client.phone or '-'}</td>
            <td>{client.created_at.strftime('%d.%m.%Y') if client.created_at else '-'}</td>
            <td>{bookings_count}</td>
        </tr>
        """
    
    if not clients:
        clients_html = '<tr><td colspan="6" style="text-align: center;">Нет клиентов</td></tr>'
    
    content = f"""
    <h1>👥 Список клиентов</h1>
    <div class="card">
        <table>
            <thead><tr><th>ID</th><th>Telegram ID</th><th>Имя</th><th>Телефон</th><th>Дата регистрации</th><th>Записей</th></tr></thead>
            <tbody>{clients_html}</tbody>
        </table>
    </div>
    """
    return render_page("Клиенты", content)

# ============ ОТЧЁТЫ ============
@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    total_consultations = db.query(Booking).filter(Booking.payment_status == 'paid').count()
    total_bookings = db.query(Booking).count()
    conversion_rate = round((total_consultations / total_bookings * 100) if total_bookings > 0 else 0)
    
    services = db.query(Service).all()
    services_html = ""
    for service in services:
        count = db.query(Booking).filter_by(service_id=service.id, payment_status='paid').count()
        revenue = count * service.price_rub
        services_html += f"<tr><td>{service.name}</td><td>{count}</td><td>{revenue}₽</td></tr>"
    
    if not services:
        services_html = '<tr><td colspan="3" style="text-align: center;">Нет данных</td></tr>'
    
    content = f"""
    <h1>📊 Аналитика и отчёты</h1>
    <div class="stats">
        <div class="stat-card"><div class="stat-number">{total_consultations}</div><div class="stat-label">Всего консультаций</div></div>
        <div class="stat-card"><div class="stat-number">{conversion_rate}%</div><div class="stat-label">Конверсия в оплату</div></div>
    </div>
    <div class="card">
        <h3>Доход по услугам</h3>
        <table><thead><tr><th>Услуга</th><th>Количество</th><th>Доход</th></tr></thead>
        <tbody>{services_html}</tbody></table>
    </div>
    """
    return render_page("Отчёты", content)

# ============ НАСТРОЙКИ ============
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    services = db.query(Service).all()
    services_html = ""
    for service in services:
        services_html += f"""
        <tr>
            <td>{service.id}</td>
            <td>{service.name}</td>
            <td>{service.price_rub}₽</td>
            <td>{"✅ Активна" if service.is_active else "❌ Неактивна"}</td>
        </tr>
        """
    
    if not services:
        services_html = '<tr><td colspan="4" style="text-align: center;">Нет услуг</td></tr>'
    
    content = f"""
    <h1>⚙️ Настройки системы</h1>
    <div class="card">
        <h3>Управление услугами</h3>
        <table><thead><tr><th>ID</th><th>Название</th><th>Цена (RUB)</th><th>Статус</th></tr></thead>
        <tbody>{services_html}</tbody></table>
    </div>
    """
    return render_page("Настройки", content)

# ============ ВЫХОД ============
@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("admin_token")
    return response

if __name__ == "__main__":
    print("🚀 Запуск админ-панели...")
    print("📊 Админка доступна по адресу: http://localhost:8000")
    print("🔑 Пароль: admin123")
    uvicorn.run(app, host="0.0.0.0", port=8000)