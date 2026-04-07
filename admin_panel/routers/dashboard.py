from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from datetime import datetime, timedelta

from templates_config import templates
from dependencies.auth import require_auth
from dependencies.database import get_db
from models import User, Booking, Service

router = APIRouter(prefix="/admin", tags=["dashboard"])



@router.get("/dashboard", response_class=HTMLResponse)
@require_auth
async def dashboard(
        request: Request,
        db=Depends(get_db)
):
    # Статистика
    total_clients = await db.scalar(select(func.count()).select_from(User).where(User.role == "client"))

    # Активные сопровождения
    today = datetime.now().date()
    active_support = await db.scalar(
        select(func.count()).select_from(Booking)
        .where(Booking.support_end_date > today)
    )

    # Доход за месяц
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    monthly_revenue = await db.scalar(
        select(func.sum(Service.price_rub))
        .select_from(Booking)
        .join(Service)
        .where(
            Booking.payment_status == "paid",
            Booking.confirmed_at >= month_start
        )
    ) or 0

    # Ожидающие подтверждения
    pending_payments = await db.scalar(
        select(func.count()).select_from(Booking)
        .where(Booking.payment_status == "waiting_confirm")
    )

    # Консультации на сегодня
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    today_end = today_start + timedelta(days=1)
    today_consults = await db.scalar(
        select(func.count()).select_from(Booking)
        .where(
            Booking.consultation_datetime >= today_start,
            Booking.consultation_datetime < today_end,
            Booking.payment_status == "paid"
        )
    )

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_clients": total_clients or 0,
        "active_support": active_support or 0,
        "monthly_revenue": monthly_revenue,
        "pending_payments": pending_payments or 0,
        "today_consults": today_consults or 0
    })