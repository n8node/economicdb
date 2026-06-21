from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.etl.calendar.options import DEFAULT_CALENDAR_SOURCES


class CalendarSyncRequest(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    sources: list[str] = Field(default_factory=lambda: list(DEFAULT_CALENDAR_SOURCES))
    enrich: bool = True
    dry_run: bool = False


class CalendarEnrichRequest(BaseModel):
    dry_run: bool = False


class CalendarSyncResult(BaseModel):
    ok: bool
    job_id: int | None = None
    message: str | None = None
    records: int | None = None
    enriched: int | None = None
    sources: dict[str, int] | None = None
    skipped: list[dict] | None = None
    date_from: str | None = None
    date_to: str | None = None
    error: str | None = None


class CalendarStatsResponse(BaseModel):
    total: int
    upcoming: int
    past: int
    with_actual: int
    with_forecast: int
    by_source: dict[str, int]
    by_country: dict[str, int]


class CalendarSourceInfo(BaseModel):
    id: str
    label: str
    description: str
    requires_api_key: bool
    tier: str


class CalendarSourcesResponse(BaseModel):
    sources: list[CalendarSourceInfo]
    default_sources: list[str]
