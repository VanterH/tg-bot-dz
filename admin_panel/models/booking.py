from sqlalchemy import Integer, String, ForeignKey, TIMESTAMP, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date

from models.base import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    payment_status: Mapped[str | None] = mapped_column(String(50))
    payment_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    payment_proof_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    admin_confirmed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True
    )
    consultation_datetime: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True
    )
    support_end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )
    is_program_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=datetime.utcnow
    )

    # Связи
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="bookings"
    )

    admin_confirmer = relationship(
        "User",
        foreign_keys=[admin_confirmed_by],
        back_populates="confirmed_bookings"
    )

    service = relationship("Service", back_populates="bookings")
    slot = relationship("ScheduleSlot", back_populates="booking", uselist=False)