from sqlalchemy import Integer, ForeignKey, TIMESTAMP, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from models.base import Base


class ScheduleSlot(Base):
    __tablename__ = "schedule_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_datetime: Mapped[datetime] = mapped_column(TIMESTAMP)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)
    booking_id: Mapped[int | None] = mapped_column(
        ForeignKey("bookings.id"),
        nullable=True
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    # Связи
    booking = relationship("Booking", back_populates="slot")
    creator = relationship("User", back_populates="created_slots")