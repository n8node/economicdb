from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


CALENDAR_PROVIDER_ID = "calendar"

DEFAULT_CALENDAR_SOURCES = ("fred", "cbr", "ecb", "rosstat", "fomc")


@dataclass
class CalendarSyncOptions:
    date_from: date | None = None
    date_to: date | None = None
    sources: list[str] = field(default_factory=lambda: list(DEFAULT_CALENDAR_SOURCES))
    enrich: bool = True
    dry_run: bool = False
    trigger: str = "manual"
    admin_id: int | None = None
