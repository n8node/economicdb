from __future__ import annotations

from calendar import monthrange
from datetime import date

from app.etl.calendar.mappings import ROSSTAT_RELEASE_MAPPINGS, event_id, msk_datetime
from app.etl.calendar.writer import CalendarEventDraft


async def fetch_rosstat_calendar_events(*, date_from: date, date_to: date) -> list[CalendarEventDraft]:
    drafts: list[CalendarEventDraft] = []
    cursor = date(date_from.year, date_from.month, 1)
    end = date(date_to.year, date_to.month, monthrange(date_to.year, date_to.month)[1])

    while cursor <= end:
        for mapping in ROSSTAT_RELEASE_MAPPINGS:
            day = min(mapping.day_of_month, monthrange(cursor.year, cursor.month)[1])
            release_day = date(cursor.year, cursor.month, day)
            if release_day < date_from or release_day > date_to:
                continue
            drafts.append(
                CalendarEventDraft(
                    id=event_id("rosstat", mapping.slug, release_day),
                    title_ru=mapping.title_ru,
                    country="ru",
                    category=mapping.category,
                    importance=mapping.importance,
                    scheduled_at_msk=msk_datetime(release_day, mapping.hour, mapping.minute),
                    source="rosstat",
                    linked_indicator_id=mapping.linked_indicator_id,
                    unit="%",
                )
            )
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)

    return drafts
