# web_admin/simple_app.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uvicorn
import json

from database.db import SessionLocal, get_db
from database.models import User, Service, Booking, ScheduleSlot, Question, PaymentRequest, ArchiveEntry, ExpertLog

app = FastAPI()
ADMIN_PASSWORD = "admin123"

# Базовый HTML шаблон
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background: #f5f5f5; }}
        .sidebar {{
            width: 260px;
            background: #2c3e50;
            color: white;
            position: fixed;
            height: 100%;
            padding: 20px;
            overflow-y: auto;
        }}
        .sidebar h2 {{ margin-bottom: 30px; font-size: 20px; text-align: center; }}
        .sidebar a {{
            color: white;
            text-decoration: none;
            display: block;
            padding: 12px;
            margin: 5px 0;
            border-radius: 8px;
            transition: all 0.3s;
        }}
        .sidebar a:hover {{ background: #34495e; }}
        .sidebar .section-title {{
            font-size: 11px;
            text-transform: uppercase;
            color: #95a5a6;
            margin-top: 20px;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }}
        .content {{
            margin-left: 260px;
            padding: 30px;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{ color: #7f8c8d; margin-top: 10px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        tr:hover {{ background: #f8f9fa; }}
        .btn {{
            padding: 6px 12px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            margin: 2px;
            text-decoration: none;
            display: inline-block;
            transition: all 0.2s;
        }}
        .btn-success {{ background: #27ae60; color: white; }}
        .btn-success:hover {{ background: #219a52; }}
        .btn-danger {{ background: #e74c3c; color: white; }}
        .btn-danger:hover {{ background: #c0392b; }}
        .btn-primary {{ background: #3498db; color: white; }}
        .btn-primary:hover {{ background: #2980b9; }}
        .btn-warning {{ background: #f39c12; color: white; }}
        .btn-warning:hover {{ background: #e67e22; }}
        .status {{
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            display: inline-block;
        }}
        .status-paid, .status-answered {{ background: #27ae60; color: white; }}
        .status-waiting_confirm, .status-expert_review {{ background: #f39c12; color: white; }}
        .status-pending, .status-received {{ background: #95a5a6; color: white; }}
        .status-rejected {{ background: #e74c3c; color: white; }}
        h1 {{ margin-bottom: 24px; color: #2c3e50; font-size: 28px; }}
        .filter-bar {{ margin-bottom: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
        input, select, textarea {{ padding: 8px 12px; margin-right: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }}
        .form-group {{ margin-bottom: 20px; }}
        .form-group label {{ display: block; margin-bottom: 8px; font-weight: 600; }}
        .form-group input, .form-group select, .form-group textarea {{ padding: 10px; width: 100%; max-width: 400px; border: 1px solid #ddd; border-radius: 6px; }}
        pre {{
            white-space: pre-wrap;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.5;
        }}
        .btn-warning {{
            background: #f39c12;
            color: white;
        }}
        .btn-warning:hover {{
            background: #e67e22;
        }}
        .message-success {{ background: #d4edda; color: #155724; padding: 12px; border-radius: 8px; margin-bottom: 20px; }}
        .message-error {{ background: #f8d7da; color: #721c24; padding: 12px; border-radius: 8px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>🌿 doTERRA Admin</h2>
        <div class="section-title">ОСНОВНОЕ</div>
        <a href="/">📈 Дашборд</a>
        <div class="section-title">КОНСУЛЬТАЦИИ</div>
        <a href="/bookings">📋 Заявки на консультацию</a>
        <a href="/schedule">📅 Расписание</a>
        <a href="/services">💰 Услуги</a>
        <div class="section-title">ВОПРОСЫ ЭКСПЕРТУ</div>
        <a href="/questions">❓ Вопросы</a>
        <a href="/payments">💳 Оплаты вопросов</a>
        <a href="/archive">📋 Архив ответов</a>
        <div class="section-title">ПОЛЬЗОВАТЕЛИ</div>
        <a href="/users">👥 Пользователи</a>
        <div class="section-title">СИСТЕМА</div>
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
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
            border-radius: 16px;
            width: 380px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        h2 {{ text-align: center; margin-bottom: 30px; color: #333; }}
        input {{ width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }}
        button {{ width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; transition: background 0.3s; }}
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


# ============ ДАШБОРД ============
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    # Статистика
    total_users = db.query(User).count()
    total_bookings = db.query(Booking).count()
    pending_bookings = db.query(Booking).filter_by(payment_status='waiting_confirm').count()
    total_slots = db.query(ScheduleSlot).count()
    
    total_questions = db.query(Question).count()
    pending_questions = db.query(Question).filter_by(status='expert_review').count()
    total_payments = db.query(PaymentRequest).filter_by(status='confirmed').count()
    
    confirmed_bookings = db.query(Booking).filter_by(payment_status='paid').all()
    bookings_revenue = sum(b.service.price_rub if b.service else 0 for b in confirmed_bookings)
    
    content = f"""
    <h1>📈 Дашборд</h1>
    <div class="stats">
        <div class="stat-card"><div class="stat-number">{total_users}</div><div class="stat-label">Пользователей</div></div>
        <div class="stat-card"><div class="stat-number">{total_bookings}</div><div class="stat-label">Всего записей</div></div>
        <div class="stat-card"><div class="stat-number">{pending_bookings}</div><div class="stat-label">Ожидают оплаты</div></div>
        <div class="stat-card"><div class="stat-number">{total_slots}</div><div class="stat-label">Слотов расписания</div></div>
        <div class="stat-card"><div class="stat-number">{total_questions}</div><div class="stat-label">Всего вопросов</div></div>
        <div class="stat-card"><div class="stat-number">{pending_questions}</div><div class="stat-label">Вопросов в обработке</div></div>
        <div class="stat-card"><div class="stat-number">{total_payments}</div><div class="stat-label">Оплат вопросов</div></div>
        <div class="stat-card"><div class="stat-number">{bookings_revenue}₽</div><div class="stat-label">Доход с консультаций</div></div>
    </div>
    """
    return render_page("Дашборд", content)


# ============ ЗАЯВКИ НА КОНСУЛЬТАЦИЮ ============
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
        if b.payment_proof_url:
            # Используем правильный маршрут /receipt/{id}
            receipt_link = f'<a href="/receipt/{b.id}" target="_blank" class="btn btn-info">📷 Чек</a>'
        else:
            receipt_link = '<span style="color: #999;">Нет чека</span>'
        
        
        if b.payment_status == 'waiting_confirm':
            action_buttons = f'''
                <form method="post" action="/confirm_booking/{b.id}" style="display:inline">
                    <button type="submit" class="btn btn-success">✅ Подтвердить</button>
                </form>
                <form method="post" action="/reject_booking/{b.id}" style="display:inline">
                    <button type="submit" class="btn btn-danger">❌ Отклонить</button>
                </form>
                <form method="post" action="/delete_booking/{b.id}" style="display:inline" 
                    onsubmit="return confirm('Удалить запись? Пользователь получит уведомление.')">
                    <button type="submit" class="btn btn-warning">🗑️ Удалить</button>
                </form>
            '''
        elif b.payment_status == 'paid':
            action_buttons = f'''
                <form method="post" action="/delete_booking/{b.id}" style="display:inline" 
                    onsubmit="return confirm('Удалить запись? Пользователь получит уведомление.')">
                    <button type="submit" class="btn btn-warning">🗑️ Удалить</button>
                </form>
            '''
        else:
            action_buttons = f'''
                <form method="post" action="/delete_booking/{b.id}" style="display:inline" 
                    onsubmit="return confirm('Удалить запись? Пользователь получит уведомление.')">
                    <button type="submit" class="btn btn-warning">🗑️ Удалить</button>
                </form>
            '''
        
        table_html += f"""
        <tr>
            <td>{b.id}</td>
            <td>{user.first_name or user.username if user else '-'}</td>
            <td>{service.name if service else '-'}</td>
            <td>{service.price_rub if service else 0}₽</td>
            <td><span class="status status-{b.payment_status}">{b.payment_status}</span></td>
            <td>{b.created_at.strftime('%d.%m.%Y %H:%M') if b.created_at else '-'}</td>
            <td>{receipt_link}</td>
            <td>{action_buttons}</td>
        </tr>
        """
    
    if not bookings:
        table_html = '<tr><td colspan="8" style="text-align: center; color: #999;">Нет заявок</td></tr>'
    
    content = f"""
    <h1>📋 Заявки на консультацию</h1>
    <div class="card">
        <div class="filter-bar">
            <input type="text" placeholder="Поиск...">
            <select><option>Все статусы</option></select>
            <button class="btn btn-primary">Поиск</button>
        </div>
        <table>
            <thead><tr><th>ID</th><th>Клиент</th><th>Услуга</th><th>Сумма</th><th>Статус</th><th>Дата</th><th>Чек</th><th>Действие</th></tr></thead>
            <tbody>{table_html}</tbody>
        </table>
    </div>
    """
    return render_page("Заявки", content)


@app.post("/confirm_booking/{booking_id}")
async def confirm_booking(booking_id: int, request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    booking = db.query(Booking).get(booking_id)
    if booking:
        booking.payment_status = 'paid'
        booking.confirmed_at = datetime.now()
        db.commit()
        
        # Отправляем уведомление пользователю
        user = db.query(User).get(booking.user_id)
        if user and user.telegram_id:
            try:
                from aiogram import Bot
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                
                bot_token = os.getenv('BOT_TOKEN')
                bot = Bot(token=bot_token) if bot_token else None
                
                if bot:
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📅 Выбрать время", callback_data="choose_slot")]
                    ])
                    await bot.send_message(
                        user.telegram_id,
                        f"✅ <b>Оплата подтверждена!</b>\n\nТеперь выберите время для консультации.",
                        reply_markup=kb,
                        parse_mode="HTML"
                    )
                    await bot.session.close()
            except Exception as e:
                print(f"Ошибка: {e}")
    
    return RedirectResponse("/bookings", status_code=303)


@app.get("/receipt/{booking_id}")
async def view_receipt(booking_id: int, request: Request, db: Session = Depends(get_db)):
    """Просмотр фото чека"""
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    booking = db.query(Booking).get(booking_id)
    if not booking or not booking.payment_proof_url:
        return HTMLResponse("<h3>❌ Чек не найден</h3>", status_code=404)
    
    # Получаем путь к файлу
    file_path = booking.payment_proof_url
    
    # Проверяем существует ли файл
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/jpeg")
    else:
        # Пробуем найти файл в папке uploads
        filename = os.path.basename(file_path)
        alt_path = os.path.join("uploads", filename)
        if os.path.exists(alt_path):
            return FileResponse(alt_path, media_type="image/jpeg")
        
        return HTMLResponse(f"<h3>❌ Файл не найден: {file_path}</h3>", status_code=404)



@app.post("/reject_booking/{booking_id}")
async def reject_booking(booking_id: int, request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    booking = db.query(Booking).get(booking_id)
    if booking:
        booking.payment_status = 'rejected'
        db.commit()
        
        user = db.query(User).get(booking.user_id)
        if user and user.telegram_id:
            try:
                from aiogram import Bot
                bot_token = os.getenv('BOT_TOKEN')
                bot = Bot(token=bot_token) if bot_token else None
                if bot:
                    await bot.send_message(user.telegram_id, "❌ Ваша оплата отклонена. Свяжитесь с администратором.")
                    await bot.session.close()
            except:
                pass
    
    return RedirectResponse("/bookings", status_code=303)


# ============ РАСПИСАНИЕ ============
@app.get("/schedule", response_class=HTMLResponse)
async def schedule_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    slots = db.query(ScheduleSlot).order_by(ScheduleSlot.slot_datetime).all()
    
    slots_html = ""
    for slot in slots:
        client_name = "-"
        if slot.is_booked and slot.booking_id:
            booking = db.query(Booking).get(slot.booking_id)
            if booking:
                user = db.query(User).get(booking.user_id)
                if user:
                    client_name = user.first_name or user.username
        
        slots_html += f"""
        <tr>
            <td>{slot.id}</td>
            <td>{slot.slot_datetime.strftime('%d.%m.%Y %H:%M') if slot.slot_datetime else '-'}</td>
            <td>{"🔴 Занят" if slot.is_booked else "🟢 Свободен"}</td>
            <td>{client_name}</td>
            <td>
                <form method="post" action="/delete_slot/{slot.id}" style="display:inline" onsubmit="return confirm('Удалить слот?')">
                    <button type="submit" class="btn btn-danger">🗑️ Удалить</button>
                </form>
            </td>
        </tr>
        """
    
    if not slots:
        slots_html = '<tr><td colspan="5" style="text-align: center; color: #999;">Нет слотов</td></tr>'
    
    content = f"""
    <h1>📅 Управление расписанием</h1>
    <div class="card">
        <h3>➕ Добавить слот</h3>
        <form method="post" action="/add_slot">
            <div class="form-group"><label>Дата:</label><input type="date" name="date" required></div>
            <div class="form-group"><label>Время:</label><input type="time" name="time" required></div>
            <button type="submit" class="btn btn-primary">➕ Добавить</button>
        </form>
    </div>
    <div class="card">
        <h3>📋 Текущие слоты</h3>
        <table>
            <thead><tr><th>ID</th><th>Дата и время</th><th>Статус</th><th>Клиент</th><th>Действие</th></tr></thead>
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
    
    try:
        slot_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        slot = ScheduleSlot(slot_datetime=slot_datetime, is_booked=False)
        db.add(slot)
        db.commit()
    except Exception as e:
        pass
    
    return RedirectResponse("/schedule", status_code=303)


@app.post("/delete_slot/{slot_id}")
async def delete_slot(slot_id: int, request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    slot = db.query(ScheduleSlot).get(slot_id)
    if slot:
        # Если слот был забронирован, уведомляем пользователя
        if slot.is_booked and slot.booking_id:
            booking = db.query(Booking).get(slot.booking_id)
            if booking:
                user = db.query(User).get(booking.user_id)
                if user and user.telegram_id:
                    try:
                        from aiogram import Bot
                        bot_token = os.getenv('BOT_TOKEN')
                        bot = Bot(token=bot_token) if bot_token else None
                        
                        if bot:
                            await bot.send_message(
                                user.telegram_id,
                                f"⚠️ <b>Ваша запись на консультацию отменена администратором</b>\n\n"
                                f"📅 Запланированное время: {slot.slot_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
                                f"Пожалуйста, выберите новое время в боте.",
                                parse_mode="HTML"
                            )
                            await bot.session.close()
                    except Exception as e:
                        print(f"Ошибка отправки уведомления: {e}")
        
        db.delete(slot)
        db.commit()
    
    return RedirectResponse("/schedule", status_code=303)


@app.post("/cancel_booking/{booking_id}")
async def cancel_booking(booking_id: int, request: Request, db: Session = Depends(get_db)):
    """Отмена записи на консультацию"""
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    booking = db.query(Booking).get(booking_id)
    if booking:
        user = db.query(User).get(booking.user_id)
        
        # Освобождаем слот если был
        if booking.consultation_datetime:
            slot = db.query(ScheduleSlot).filter_by(
                slot_datetime=booking.consultation_datetime,
                is_booked=True
            ).first()
            if slot:
                slot.is_booked = False
                slot.booking_id = None
        
        # Удаляем запись
        db.delete(booking)
        db.commit()
        
        # Уведомляем пользователя
        if user and user.telegram_id:
            try:
                from aiogram import Bot
                bot_token = os.getenv('BOT_TOKEN')
                bot = Bot(token=bot_token) if bot_token else None
                
                if bot:
                    await bot.send_message(
                        user.telegram_id,
                        f"⚠️ <b>Ваша запись была отменена администратором</b>\n\n"
                        f"Вы можете создать новую запись в боте.",
                        parse_mode="HTML"
                    )
                    await bot.session.close()
            except Exception as e:
                print(f"Ошибка: {e}")
    
    return RedirectResponse("/bookings", status_code=303)

# ============ УСЛУГИ ============
@app.get("/services", response_class=HTMLResponse)
async def services_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    services = db.query(Service).all()
    
    table_html = ""
    for s in services:
        table_html += f"""
        <tr>
            <td>{s.id}</td>
            <td>{s.name}</td>
            <td>{s.price_rub}₽</td><td>{s.price_usd}$</td>
            <td>{s.support_days} дней</td>
            <td>{"✅ Активна" if s.is_active else "❌ Неактивна"}</td>
            <td>
                <form method="post" action="/update_service_price/{s.id}" style="display:inline">
                    <input type="number" name="price_rub" value="{s.price_rub}" style="width:80px">
                    <button type="submit" class="btn btn-primary">Обновить</button>
                </form>
            </td>
        </tr>
        """
    
    if not services:
        table_html = '<tr><td colspan="7" style="text-align: center; color: #999;">Нет услуг</td></tr>'
    
    content = f"""
    <h1>💰 Управление услугами</h1>
    <div class="card">
        <h3>➕ Добавить услугу</h3>
        <form method="post" action="/add_service">
            <div class="form-group"><label>Название:</label><input type="text" name="name" required></div>
            <div class="form-group"><label>Цена (RUB):</label><input type="number" name="price_rub" required></div>
            <div class="form-group"><label>Цена (USD):</label><input type="number" name="price_usd" required></div>
            <div class="form-group"><label>Дней сопровождения:</label><input type="number" name="support_days" value="0"></div>
            <button type="submit" class="btn btn-primary">➕ Добавить</button>
        </form>
    </div>
    <div class="card">
        <h3>📋 Список услуг</h3>
        <table>
            <thead><tr><th>ID</th><th>Название</th><th>Цена (RUB)</th><th>Цена (USD)</th><th>Сопровождение</th><th>Статус</th><th>Действие</th></tr></thead>
            <tbody>{table_html}</tbody>
        </table>
    </div>
    """
    return render_page("Услуги", content)


@app.post("/add_service")
async def add_service(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    form = await request.form()
    service = Service(
        name=form.get('name'),
        price_rub=int(form.get('price_rub')),
        price_usd=int(form.get('price_usd')),
        support_days=int(form.get('support_days', 0)),
        is_active=True
    )
    db.add(service)
    db.commit()
    
    return RedirectResponse("/services", status_code=303)


@app.post("/update_service_price/{service_id}")
async def update_service_price(service_id: int, request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    form = await request.form()
    service = db.query(Service).get(service_id)
    if service:
        service.price_rub = int(form.get('price_rub'))
        db.commit()
    
    return RedirectResponse("/services", status_code=303)


# ============ ВОПРОСЫ ЭКСПЕРТУ ============
@app.get("/questions", response_class=HTMLResponse)
async def questions_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    questions = db.query(Question).order_by(Question.created_at.desc()).all()
    
    table_html = ""
    for q in questions:
        user = db.query(User).get(q.user_id)
        is_answered_class = "status-answered" if q.status == 'answered' else "status-expert_review"
        table_html += f"""
        <tr>
            <td>{q.id}</td>
            <td>{user.first_name or user.username if user else '-'}</td>
            <td>{q.topic or '-'}</td>
            <td><span class="status {is_answered_class}">{q.status}</span></td>
            <td>{q.created_at.strftime('%d.%m.%Y %H:%M') if q.created_at else '-'}</td>
            <td>
                <a href="/question_detail/{q.id}" class="btn btn-primary">📖 Просмотр</a>
            </td>
        </tr>
        """
    
    if not questions:
        table_html = '<tr><td colspan="6" style="text-align: center; color: #999;">Нет вопросов</td></tr>'
    
    content = f"""
    <h1>❓ Вопросы эксперту</h1>
    <div class="card">
        <div class="filter-bar">
            <input type="text" placeholder="Поиск...">
            <select><option>Все статусы</option></select>
            <button class="btn btn-primary">Поиск</button>
        </div>
        <table>
            <thead><tr><th>ID</th><th>Пользователь</th><th>Тема</th><th>Статус</th><th>Дата</th><th>Действие</th></tr></thead>
            <tbody>{table_html}</tbody>
        </table>
    </div>
    """
    return render_page("Вопросы", content)


@app.get("/question_detail/{question_id}", response_class=HTMLResponse)
async def question_detail(request: Request, question_id: str, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    q = db.query(Question).get(question_id)
    if not q:
        return HTMLResponse("<h3>Вопрос не найден</h3>")
    
    user = db.query(User).get(q.user_id)
    is_answered = q.status == 'answered'
    answer_value = q.final_answer if q.final_answer else ''
    
    content = f"""
    <h1>📋 Вопрос #{q.id}</h1>
    
    <div class="card">
        <h3>👤 Пользователь</h3>
        <p><strong>Имя:</strong> {user.first_name or user.username if user else '-'}<br>
        <strong>Email:</strong> {user.email or '-'}<br>
        <strong>Telegram ID:</strong> {user.telegram_id if user else '-'}</p>
    </div>
    
    <div class="card">
        <h3>❓ Вопрос</h3>
        <pre>{q.text}</pre>
    </div>
    
    <div class="card">
        <h3>🤖 Ответ ИИ (YandexGPT)</h3>
        <p><strong>Уверенность:</strong> {int(q.rag_confidence * 100) if q.rag_confidence else 0}%</p>
        <pre>{q.rag_answer or 'Не сгенерирован'}</pre>
        <p><strong>Источники:</strong></p>
        <ul>{''.join([f'<li>{s}</li>' for s in (q.rag_sources or [])])}</ul>
    </div>
    
    <div class="card">
        <h3>✏️ {'Редактировать ответ' if is_answered else 'Дополнить ответ'}</h3>
        <form method="post" action="/update_and_notify/{q.id}">
            <div class="form-group">
                <label>Ответ пользователю:</label>
                <textarea name="answer" rows="12" style="width: 100%; padding: 10px; font-family: monospace;">{answer_value or q.rag_answer or ''}</textarea>
            </div>
            <div class="form-group">
                <label>Комментарий для пользователя (опционально):</label>
                <textarea name="comment" rows="3" style="width: 100%; padding: 10px;" placeholder="Дополнительный комментарий к ответу..."></textarea>
            </div>
            <div class="form-group">
                <label>Уведомить пользователя:</label>
                <input type="checkbox" name="notify_user" value="true" checked>
            </div>
            <button type="submit" class="btn btn-success">💾 {'Обновить и отправить' if is_answered else 'Дополнить и отправить'}</button>
            <a href="/questions" class="btn btn-primary">◀️ Назад</a>
        </form>
    </div>
    """
    return render_page(f"Вопрос {q.id}", content)


@app.post("/update_and_notify/{question_id}")
async def update_and_notify(question_id: str, request: Request, db: Session = Depends(get_db)):
    """Обновление ответа и отправка уведомления пользователю"""
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    form = await request.form()
    answer = form.get('answer')
    comment = form.get('comment')
    notify_user = form.get('notify_user') == 'true'
    
    q = db.query(Question).get(question_id)
    if not q or not answer:
        return RedirectResponse(f"/question_detail/{question_id}", status_code=303)
    
    old_answer = q.final_answer
    
    # Обновляем вопрос
    q.final_answer = answer
    if q.status != 'answered':
        q.status = 'answered'
        q.answered_at = datetime.now()
        user = db.query(User).get(q.user_id)
        if user:
            user.questions_used += 1
    
    # Сохраняем в архив
    existing_archive = db.query(ArchiveEntry).filter_by(question_id=question_id).first()
    if not existing_archive:
        archive = ArchiveEntry(
            question_id=q.id,
            user_id=q.user_id,
            question_text=q.text,
            final_answer=answer,
            topics=[q.topic] if q.topic else []
        )
        db.add(archive)
    
    # Логируем действие
    expert_log = ExpertLog(
        expert_id=None,
        question_id=question_id,
        action='admin_edit',
        old_answer=old_answer[:500] if old_answer else None,
        new_answer=answer[:500],
        revision_notes=comment
    )
    db.add(expert_log)
    db.commit()
    
    # Отправляем уведомление
    if notify_user:
        user = db.query(User).get(q.user_id)
        if user and user.telegram_id:
            try:
                from aiogram import Bot
                bot_token = os.getenv('BOT_TOKEN')
                bot = Bot(token=bot_token) if bot_token else None
                
                if bot:
                    message_text = f"✅ <b>Ответ на ваш вопрос дополнен!</b>\n\n📋 ID вопроса: {question_id}\n\n💬 <b>Ответ:</b>\n{answer[:800]}\n\n"
                    if comment:
                        message_text += f"📝 <b>Комментарий:</b>\n{comment}\n\n"
                    message_text += "Используйте /archive для просмотра всех ответов."
                    
                    await bot.send_message(user.telegram_id, message_text, parse_mode="HTML")
                    await bot.session.close()
            except Exception as e:
                print(f"Ошибка отправки: {e}")
    
    return RedirectResponse(f"/question_detail/{question_id}", status_code=303)


# ============ ОПЛАТЫ ВОПРОСОВ ============
@app.get("/payments", response_class=HTMLResponse)
async def payments_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    payments = db.query(PaymentRequest).order_by(PaymentRequest.created_at.desc()).all()
    
    table_html = ""
    for p in payments:
        user = db.query(User).get(p.user_id)
        table_html += f"""
        <tr>
            <td>{p.id}</td>
            <td>{user.first_name or user.username if user else '-'}</td>
            <td>{p.plan}</td>
            <td>{p.amount_rub}₽</td>
            <td><span class="status status-{'paid' if p.status == 'confirmed' else 'waiting_confirm'}">{p.status}</span></td>
            <td>{p.created_at.strftime('%d.%m.%Y %H:%M') if p.created_at else '-'}</td>
            <td>
                <form method="post" action="/confirm_payment/{p.id}" style="display:inline">
                    <button type="submit" class="btn btn-success">✅ Подтвердить</button>
                </form>
                <form method="post" action="/reject_payment/{p.id}" style="display:inline">
                    <button type="submit" class="btn btn-danger">❌ Отклонить</button>
                </form>
            </td>
        </tr>
        """
    
    if not payments:
        table_html = '<tr><td colspan="7" style="text-align: center; color: #999;">Нет платежей</td></tr>'
    
    content = f"""
    <h1>💳 Оплаты вопросов</h1>
    <div class="card">
        <table>
            <thead><tr><th>ID</th><th>Пользователь</th><th>Тариф</th><th>Сумма</th><th>Статус</th><th>Дата</th><th>Действие</th></tr></thead>
            <tbody>{table_html}</tbody>
        </table>
    </div>
    """
    return render_page("Платежи", content)


@app.post("/confirm_payment/{payment_id}")
async def confirm_payment(payment_id: int, request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    payment = db.query(PaymentRequest).get(payment_id)
    if payment:
        payment.status = 'confirmed'
        payment.confirmed_at = datetime.now()
        
        user = db.query(User).get(payment.user_id)
        if user:
            user.subscription_plan = payment.plan
            user.questions_total = payment.questions_count
            user.questions_used = 0
            user.subscription_status = 'active'
            if payment.valid_days > 0:
                user.subscription_valid_until = datetime.now() + timedelta(days=payment.valid_days)
            db.commit()
    
    return RedirectResponse("/payments", status_code=303)


@app.post("/reject_payment/{payment_id}")
async def reject_payment(payment_id: int, request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    payment = db.query(PaymentRequest).get(payment_id)
    if payment:
        payment.status = 'rejected'
        db.commit()
    
    return RedirectResponse("/payments", status_code=303)


# ============ ПОЛЬЗОВАТЕЛИ ============
@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    table_html = ""
    for u in users:
        bookings_count = db.query(Booking).filter_by(user_id=u.id).count()
        questions_count = db.query(Question).filter_by(user_id=u.id).count()
        
        table_html += f"""
        <tr>
            <td>{u.id}</td>
            <td>{u.telegram_id}</td>
            <td>{u.first_name or u.username or '-'}</td>
            <td>{u.email or '-'}</td>
            <td>{u.subscription_plan or '-'}</td>
            <td>{u.questions_used}/{u.questions_total}</td>
            <td>{bookings_count}</td>
            <td>{questions_count}</td>
        </tr>
        """
    
    if not users:
        table_html = '<tr><td colspan="8" style="text-align: center; color: #999;">Нет пользователей</td></tr>'
    
    content = f"""
    <h1>👥 Пользователи</h1>
    <div class="card">
        <table>
            <thead><tr><th>ID</th><th>Telegram ID</th><th>Имя</th><th>Email</th><th>Тариф</th><th>Вопросы</th><th>Консультации</th><th>Всего вопросов</th></tr></thead>
            <tbody>{table_html}</tbody>
        </table>
    </div>
    """
    return render_page("Пользователи", content)


# ============ АРХИВ ============
@app.get("/archive", response_class=HTMLResponse)
async def archive_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    archives = db.query(ArchiveEntry).order_by(ArchiveEntry.created_at.desc()).all()
    
    table_html = ""
    for a in archives:
        user = db.query(User).get(a.user_id)
        table_html += f"""
        <tr>
            <td>{a.id}</td>
            <td>{a.question_id}</td>
            <td>{user.first_name or user.username if user else '-'}</td>
            <td>{a.question_text[:100]}...</td>
            <td><a href="/archive_detail/{a.id}" class="btn btn-primary">📖 Просмотр</a></td>
        </tr>
        """
    
    if not archives:
        table_html = '<tr><td colspan="5" style="text-align: center; color: #999;">Нет записей в архиве</td></tr>'
    
    content = f"""
    <h1>📋 Архив ответов</h1>
    <div class="card">
        <table>
            <thead><tr><th>ID</th><th>ID вопроса</th><th>Пользователь</th><th>Вопрос</th><th>Действие</th></tr></thead>
            <tbody>{table_html}</tbody>
        </table>
    </div>
    """
    return render_page("Архив", content)


@app.get("/archive_detail/{archive_id}", response_class=HTMLResponse)
async def archive_detail(request: Request, archive_id: int, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    a = db.query(ArchiveEntry).get(archive_id)
    if not a:
        return HTMLResponse("<h3>Запись не найдена</h3>")
    
    user = db.query(User).get(a.user_id)
    
    content = f"""
    <h1>📋 Детали архива #{a.id}</h1>
    <div class="card">
        <h3>👤 Пользователь</h3>
        <p><strong>Имя:</strong> {user.first_name or user.username if user else '-'}<br>
        <strong>Telegram ID:</strong> {user.telegram_id if user else '-'}</p>
    </div>
    <div class="card">
        <h3>❓ Вопрос</h3>
        <pre>{a.question_text}</pre>
    </div>
    <div class="card">
        <h3>💬 Ответ</h3>
        <pre>{a.final_answer}</pre>
        <a href="/archive" class="btn btn-primary">◀️ Назад</a>
    </div>
    """
    return render_page(f"Архив #{a.id}", content)


# ============ НАСТРОЙКИ ============
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    content = """
    <h1>⚙️ Настройки системы</h1>
    <div class="card">
        <h3>Общие настройки</h3>
        <form method="post" action="/update_settings">
            <div class="form-group">
                <label>Пароль администратора:</label>
                <input type="password" name="admin_password" placeholder="Новый пароль">
            </div>
            <div class="form-group">
                <label>ID экспертов (через запятую):</label>
                <input type="text" name="expert_ids" placeholder="123456789,987654321">
            </div>
            <button type="submit" class="btn btn-primary">💾 Сохранить</button>
        </form>
    </div>
    """
    return render_page("Настройки", content)

# web_admin/simple_app.py - добавьте новый эндпоинт

# web_admin/simple_app.py - исправленная функция delete_booking

@app.post("/delete_booking/{booking_id}")
async def delete_booking(booking_id: int, request: Request, db: Session = Depends(get_db)):
    """Полное удаление записи на консультацию"""
    if not verify_token(request):
        return RedirectResponse("/login", status_code=303)
    
    booking = db.query(Booking).get(booking_id)
    if not booking:
        return RedirectResponse("/bookings", status_code=303)
    
    user = db.query(User).get(booking.user_id)
    service = db.query(Service).get(booking.service_id)
    
    # Освобождаем слот если был занят
    if booking.consultation_datetime:
        slot = db.query(ScheduleSlot).filter_by(
            slot_datetime=booking.consultation_datetime,
            is_booked=True
        ).first()
        if slot:
            slot.is_booked = False
            slot.booking_id = None
            db.commit()
    
    # Отправляем уведомление пользователю с предложением выбрать новое время
    if user and user.telegram_id:
        try:
            from aiogram import Bot
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            bot_token = os.getenv('BOT_TOKEN')
            bot = Bot(token=bot_token) if bot_token else None
            
            if bot:
                # Создаем кнопку для выбора нового времени
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📅 Выбрать новое время", callback_data="choose_slot")]
                ])
                
                message_text = (
                    f"⚠️ <b>Ваша запись на консультацию была удалена администратором</b>\n\n"
                    f"📋 <b>Детали удаленной записи:</b>\n"
                    f"   🆔 ID записи: {booking.id}\n"
                    f"   📅 Услуга: {service.name if service else '-'}\n"
                    f"   💰 Сумма: {service.price_rub if service else 0}₽\n"
                    f"   📅 Статус оплаты: {booking.payment_status}\n"
                )
                
                if booking.consultation_datetime:
                    f"   ⏰ Запланированное время: {booking.consultation_datetime.strftime('%d.%m.%Y %H:%M')}\n"
                    f"\n❓ <b>Вы можете выбрать новое время для консультации:</b>"
                
                await bot.send_message(user.telegram_id, message_text, parse_mode="HTML", reply_markup=kb)
                await bot.session.close()
                print(f"✅ Уведомление отправлено пользователю {user.telegram_id}")
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления: {e}")
    
    # Удаляем запись из БД
    db.delete(booking)
    db.commit()
    
    return RedirectResponse("/bookings", status_code=303)


# ============ ВЫХОД ============
@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("admin_token")
    return response


if __name__ == "__main__":
    print("🚀 Запуск админ-панели doTERRA...")
    print("📊 Админка доступна по адресу: http://localhost:8000")
    print("🔑 Пароль: admin123")
    uvicorn.run(app, host="0.0.0.0", port=8000)