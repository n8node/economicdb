from datetime import datetime

from pydantic import BaseModel


class CalendarEventItem(BaseModel):
    id: str
    title_ru: str
    country: str
    category: str
    importance: str
    scheduled_at_msk: datetime
    scheduled_label: str
    status: str  # upcoming | past
    actual: str | None
    forecast: str | None
    previous: str | None
    surprise: str | None
    surprise_direction: str | None
    source: str
    linked_indicator_id: str | None


class CalendarIndicatorStats(BaseModel):
    min: str
    max: str
    avg: str
    median: str
    change: str
    cagr: str | None
    volatility: str
    pct_above_current: str


class CalendarEventDetail(CalendarEventItem):
    unit: str | None
    indicator_stats: CalendarIndicatorStats | None = None


class CalendarEventsResponse(BaseModel):
    items: list[CalendarEventItem]
    total: int


class CalendarSurpriseItem(BaseModel):
    id: str
    title_ru: str
    surprise: str
    surprise_direction: str
    scheduled_label: str
