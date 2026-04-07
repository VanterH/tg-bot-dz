from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload
from datetime import datetime

from templates_config import templates
from dependencies.auth import require_auth
from dependencies.database import get_db
from models import Booking, User, Service, AdminLog

router = APIRouter(prefix="/admin", tags=["bookings"])


@router.get("/bookings", response_class=HTMLResponse)
@require_auth
async def bookings_page(
        request: Request,
        status: str = Query(None),
        db=Depends(get_db)
):
    # Явно указываем, какие поля использовать для JOIN
    query = select(
        Booking,
        User.name,
        Service.name
    ).join(
        User, Booking.user_id == User.id  # 👈 Явно указываем связь
    ).join(
        Service, Booking.service_id == Service.id  # 👈 Явно указываем связь
    )

    if status:
        query = query.where(Booking.payment_status == status)

    query = query.order_by(Booking.created_at.desc())
    result = await db.execute(query)
    bookings_data = result.all()

    bookings = []
    for row in bookings_data:
        booking = row[0]  # Booking объект
        user_name = row[1]  # User.name
        service_name = row[2]  # Service.name

        bookings.append({
            "id": booking.id,
            "user_name": user_name,
            "service_name": service_name,
            "payment_status": booking.payment_status,
            "payment_currency": booking.payment_currency,
            "consultation_datetime": booking.consultation_datetime,
            "support_end_date": booking.support_end_date,
            "created_at": booking.created_at
        })

    return templates.TemplateResponse("bookings.html", {
        "request": request,
        "bookings": bookings,
        "current_status": status
    })


@router.post("/booking/{booking_id}/confirm")
@require_auth
async def confirm_booking(
        booking_id: int,
        request: Request,
        db=Depends(get_db)
):
    await db.execute(
        update(Booking)
        .where(Booking.id == booking_id)
        .values(
            payment_status="paid",
            confirmed_at=datetime.now()
        )
    )
    await db.commit()

    # Логируем действие (если таблица admin_logs существует)
    try:
        log = AdminLog(admin_id=1, action="confirm_payment", target_id=booking_id)
        db.add(log)
        await db.commit()
    except:
        pass  # Если таблицы нет, просто игнорируем

    return {"status": "success"}


@router.post("/booking/{booking_id}/reject")
@require_auth
async def reject_booking(
        booking_id: int,
        request: Request,
        db=Depends(get_db)
):
    await db.execute(
        update(Booking)
        .where(Booking.id == booking_id)
        .values(payment_status="rejected")
    )
    await db.commit()
    return {"status": "success"}