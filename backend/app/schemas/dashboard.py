from pydantic import BaseModel


class KpiItem(BaseModel):
    label: str
    value: str
    delta: str
    delta_direction: str  # up | down | flat
    sparkline: list[float] = []


class AiSummaryBlock(BaseModel):
    period: str
    headline: str
    bullets: list[str]


class CalendarEventItem(BaseModel):
    title: str
    time: str
    country: str  # ru | eu | us


class FavoriteItem(BaseModel):
    label: str
    value: str
    delta: str
    delta_direction: str
    source: str  # cbr | rosstat | fred | oecd | ecb | eurostat | imf | world_bank | moex


class ChangeItem(BaseModel):
    direction: str
    text: str
    meta: str


class DashboardOverview(BaseModel):
    updated_at: str
    kpis: list[KpiItem]
    ai_summary: AiSummaryBlock
    calendar_events: list[CalendarEventItem]
    favorites: list[FavoriteItem]
    changes: list[ChangeItem]
