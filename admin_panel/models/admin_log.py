from sqlalchemy import Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from models.base import Base


class AdminLog(Base):
    __tablename__ = "admin_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id")
    )
    action: Mapped[str] = mapped_column(String(100))
    target_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=datetime.utcnow
    )

    # Связь с админом
    admin = relationship("User", back_populates="admin_logs")