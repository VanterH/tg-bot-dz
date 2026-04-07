from fastapi import APIRouter, Request, Depends, Query, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, delete
from datetime import datetime, timedelta

from templates_config import templates
from dependencies.auth import require_auth
from dependencies.database import get_db
from models import ScheduleSlot

router = APIRouter(prefix="/admin", tags=["schedule"])



@router.get("/schedule", response_class=HTMLResponse)
@require_auth
async def schedule_page(
        request: Request,
        week_start: str = Query(None),
        db=Depends(get_db)
):
    if week_start:
        start_date = datetime.strptime(week_start, "%Y-%m-%d")
    else:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date - timedelta(days=start_date.weekday())

    end_date = start_date + timedelta(days=7)

    result = await db.execute(
        select(ScheduleSlot)
        .where(
            ScheduleSlot.slot_datetime >= start_date,
            ScheduleSlot.slot_datetime < end_date
        )
        .order_by(ScheduleSlot.slot_datetime)
    )
    slots = result.scalars().all()

    existing_slots = [slot.slot_datetime for slot in slots]

    return templates.TemplateResponse("schedule.html", {
        "request": request,
        "slots": slots,
        "start_date": start_date,
        "end_date": end_date,
        "week_start": start_date.strftime("%Y-%m-%d"),
        "existing_slots": existing_slots
    })


@router.post("/slots/upload")
@require_auth
async def upload_slots(
        request: Request,
        db=Depends(get_db)
):
    form = await request.form()
    slots_data = form.get("slots_data")

    import json
    try:
        slot_dates = json.loads(slots_data)

        for slot_date in slot_dates:
            slot_datetime = datetime.strptime(slot_date, "%Y-%m-%d %H:%M")

            existing = await db.execute(
                select(ScheduleSlot).where(ScheduleSlot.slot_datetime == slot_datetime)
            )
            if not existing.scalar_one_or_none():
                slot = ScheduleSlot(
                    slot_datetime=slot_datetime,
                    is_booked=False
                )
                db.add(slot)

        await db.commit()
        return {"status": "success", "message": f"Добавлено {len(slot_dates)} слотов"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.delete("/slot/{slot_id}")
@require_auth
async def delete_slot(
        slot_id: int,
        db=Depends(get_db)
):
    await db.execute(delete(ScheduleSlot).where(ScheduleSlot.id == slot_id))
    await db.commit()
    return {"status": "success"}