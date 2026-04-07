from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, update

from templates_config import templates
from dependencies.auth import require_auth
from dependencies.database import get_db
from models import Service
from models.schemas import ServiceUpdate

router = APIRouter(prefix="/admin", tags=["settings"])



@router.get("/settings", response_class=HTMLResponse)
@require_auth
async def settings_page(
        request: Request,
        db=Depends(get_db)
):
    result = await db.execute(select(Service))
    services = result.scalars().all()



    return templates.TemplateResponse("settings.html", {
        "request": request,
        "services": services
    })


@router.put("/settings/service/{service_id}")
@require_auth
async def update_service(
        service_id: int,
        service_data: ServiceUpdate,
        db=Depends(get_db)
):
    await db.execute(
        update(Service)
        .where(Service.id == service_id)
        .values(
            name=service_data.name,
            price_rub=service_data.price_rub,
            price_usd=service_data.price_usd,
            support_days=service_data.support_days,
            is_active=service_data.is_active
        )
    )
    await db.commit()
    return {"status": "success"}