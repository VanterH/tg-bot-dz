from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
import pandas as pd
from io import BytesIO

from templates_config import templates
from dependencies.auth import require_auth
from dependencies.database import get_db
from models import Booking, User, Service

router = APIRouter(prefix="/admin", tags=["reports"])



@router.get("/reports", response_class=HTMLResponse)
@require_auth
async def reports_page(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})


@router.get("/reports/export/excel")
@require_auth
async def export_excel(
        report_type: str = Query(...),
        db=Depends(get_db)
):
    if report_type == "revenue":
        result = await db.execute(
            select(
                Booking.confirmed_at,
                User.name.label("client_name"),
                Service.name.label("service_name"),
                Service.price_rub,
                Service.price_usd,
                Booking.payment_currency
            )
            .join(User)
            .join(Service)
            .where(Booking.payment_status == "paid")
            .order_by(Booking.confirmed_at.desc())
        )
        data = result.all()

        df = pd.DataFrame([{
            "Дата": row.confirmed_at,
            "Клиент": row.client_name,
            "Услуга": row.service_name,
            "Цена (RUB)": row.price_rub,
            "Цена (USD)": row.price_usd,
            "Валюта": row.payment_currency
        } for row in data])

    elif report_type == "consultations":
        result = await db.execute(
            select(
                Booking.consultation_datetime,
                User.name.label("client_name"),
                Service.name.label("service_name"),
                Booking.is_program_sent
            )
            .join(User)
            .join(Service)
            .where(Booking.payment_status == "paid")
            .order_by(Booking.consultation_datetime)
        )
        data = result.all()

        df = pd.DataFrame([{
            "Дата консультации": row.consultation_datetime,
            "Клиент": row.client_name,
            "Услуга": row.service_name,
            "Программа отправлена": "Да" if row.is_program_sent else "Нет"
        } for row in data])
    else:
        return {"error": "Unknown report type"}

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Report")

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={report_type}_report.xlsx"}
    )