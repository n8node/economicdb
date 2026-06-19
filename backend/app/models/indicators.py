from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.admin import Base


class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(8), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(128))
    unit: Mapped[str | None] = mapped_column(String(32))
    last_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    last_change: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndicatorValue(Base):
    __tablename__ = "indicator_values"

    indicator_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    observed_at: Mapped[date] = mapped_column(Date, primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
