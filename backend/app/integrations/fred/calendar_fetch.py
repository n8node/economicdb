from __future__ import annotations

from datetime import date

from app.etl.calendar.mappings import (
    FRED_RELEASE_MAPPINGS,
    event_id,
    us_release_datetime,
)
from app.etl.calendar.writer import CalendarEventDraft
from app.integrations.fred.client import FredError, fetch_release_dates


async def fetch_fred_calendar_events(
    api_key: str,
    *,
    date_from: date,
    date_to: date,
) -> tuple[list[CalendarEventDraft], list[dict]]:
    drafts: list[CalendarEventDraft] = []
    skipped: list[dict] = []

    for mapping in FRED_RELEASE_MAPPINGS:
        try:
            release_dates = await fetch_release_dates(
                api_key,
                mapping.release_id,
                realtime_start=date_from.isoformat(),
                realtime_end=date_to.isoformat(),
            )
        except FredError as exc:
            skipped.append({"source": "fred", "slug": mapping.slug, "reason": exc.code})
            continue

        for day in release_dates:
            if day < date_from or day > date_to:
                continue
            drafts.append(
                CalendarEventDraft(
                    id=event_id("fred", mapping.slug, day),
                    title_ru=mapping.title_ru,
                    country=mapping.country,
                    category=mapping.category,
                    importance=mapping.importance,
                    scheduled_at_msk=us_release_datetime(day),
                    source="fred",
                    linked_indicator_id=mapping.linked_indicator_id,
                    unit=mapping.unit,
                )
            )

    return drafts, skipped
