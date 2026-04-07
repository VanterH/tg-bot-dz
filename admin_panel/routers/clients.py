from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from datetime import datetime

from templates_config import templates
from dependencies.auth import require_auth
from dependencies.database import get_db
from models import User, Booking

router = APIRouter(prefix="/admin", tags=["clients"])



@router.get("/clients", response_class=HTMLResponse)
@require_auth
async def clients_page(
        request: Request,
        db=Depends(get_db)
):
    result = await db.execute(
        select(User, func.count(Booking.id).label("bookings_count"))
        .outerjoin(Booking, User.id == Booking.user_id)
        .where(User.role == "client")
        .group_by(User.id)
        .order_by(User.created_at.desc())
    )
    clients = result.all()

    clients_list = []
    for client, bookings_count in clients:
        today = datetime.now().date()
        active_booking = await db.scalar(
            select(Booking)
            .where(
                Booking.user_id == client.id,
                Booking.support_end_date > today
            )
        )

        clients_list.append({
            "id": client.id,
            "name": client.name,
            "telegram_id": client.telegram_id,
            "phone": client.phone,
            "created_at": client.created_at,
            "bookings_count": bookings_count,
            "support_end_date": active_booking.support_end_date if active_booking else None
        })

    return templates.TemplateResponse("clients.html", {
        "request": request,
        "clients": clients_list
    })