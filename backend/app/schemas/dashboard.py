from pydantic import BaseModel


class KpiItem(BaseModel):
    id: str
    label: str
    value: str
    delta: str
    delta_direction: str  # up | down | flat
    source: str
    unit: str | None = None
    frequency: str
    updated_at: str
    sparkline: list[float] = []


class AiSummaryBlock(BaseModel):
    period: str
    headline: str
    bullets: list[str]
    summary_id: str | None = None


class CalendarEventItem(BaseModel):
    title: str
    time: str
    country: str  # ru | eu | us


class ChangeItem(BaseModel):
    direction: str
    text: str
    meta: str


class DashboardOverview(BaseModel):
    updated_at: str
    kpis: list[KpiItem]
    ai_summary: AiSummaryBlock
    calendar_events: list[CalendarEventItem]
    changes: list[ChangeItem]
