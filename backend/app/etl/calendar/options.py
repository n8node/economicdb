from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from app.etl.helpers import resolve_date_range
from app.etl.options import SyncOptions


CALENDAR_PROVIDER_ID = "calendar"

DEFAULT_CALENDAR_SOURCES = ("fred", "cbr", "ecb", "rosstat", "fomc")
DEFAULT_LOOKBACK_DAYS = 90
DEFAULT_LOOKAHEAD_DAYS = 120


def resolve_calendar_date_range(options: CalendarSyncOptions | None = None) -> tuple[date, date]:
    opts = options or CalendarSyncOptions()
    if opts.date_from or opts.date_to:
        return resolve_date_range(SyncOptions(date_from=opts.date_from, date_to=opts.date_to))
    today = date.today()
    return today - timedelta(days=DEFAULT_LOOKBACK_DAYS), today + timedelta(days=DEFAULT_LOOKAHEAD_DAYS)


@dataclass
class CalendarSyncOptions:
    date_from: date | None = None
    date_to: date | None = None
    sources: list[str] = field(default_factory=lambda: list(DEFAULT_CALENDAR_SOURCES))
    enrich: bool = True
    dry_run: bool = False
    trigger: str = "manual"
    admin_id: int | None = None
