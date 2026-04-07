from sqlalchemy import Integer, String, BigInteger, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=datetime.utcnow
    )

    # Связи
    bookings = relationship(
        "Booking",
        back_populates="user",
        foreign_keys="Booking.user_id"
    )

    confirmed_bookings = relationship(
        "Booking",
        back_populates="admin_confirmer",
        foreign_keys="Booking.admin_confirmed_by"
    )

    created_slots = relationship(
        "ScheduleSlot",
        back_populates="creator",
        foreign_keys="ScheduleSlot.created_by"
    )

    admin_logs = relationship(
        "AdminLog",
        back_populates="admin",
        foreign_keys="AdminLog.admin_id"
    )