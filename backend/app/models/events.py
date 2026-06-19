from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.admin import Base


class EconomicEvent(Base):
    __tablename__ = "economic_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(8), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    importance: Mapped[str] = mapped_column(String(8), nullable=False)
    scheduled_at_msk: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    forecast: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    previous: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    surprise: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    linked_indicator_id: Mapped[str | None] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(16))
