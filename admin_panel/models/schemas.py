from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ServiceUpdate(BaseModel):
    name: str
    price_rub: int
    price_usd: int
    support_days: int
    is_active: bool

class SlotCreate(BaseModel):
    slot_datetime: datetime

class BookingResponse(BaseModel):
    id: int
    user_name: str
    service_name: str
    payment_status: str
    payment_currency: Optional[str]
    consultation_datetime: Optional[datetime]
    support_end_date: Optional[datetime]
    created_at: datetime

class ClientResponse(BaseModel):
    id: int
    name: str
    telegram_id: int
    phone: Optional[str]
    created_at: datetime
    bookings_count: int
    support_end_date: Optional[datetime]