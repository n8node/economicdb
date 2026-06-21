from __future__ import annotations

import re
from datetime import date

import httpx

from app.etl.calendar.mappings import TIER_A_EVENTS, event_id, msk_datetime
from app.etl.calendar.writer import CalendarEventDraft

FOMC_CALENDAR_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

_DATE_RE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:-\d{1,2})?,?\s+(\d{4})",
    re.IGNORECASE,
)


async def fetch_fomc_calendar_events(*, date_from: date, date_to: date) -> list[CalendarEventDraft]:
    meta = TIER_A_EVENTS["fomc"]
    meeting_days: set[date] = set()

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await client.get(FOMC_CALENDAR_URL, headers={"User-Agent": "economicdb-calendar/1.0"})
            response.raise_for_status()
            meeting_days.update(_parse_fomc_dates(response.text, date_from, date_to))
        except httpx.HTTPError:
            pass

    drafts: list[CalendarEventDraft] = []
    for day in sorted(meeting_days):
        drafts.append(
            CalendarEventDraft(
                id=event_id("fomc", meta["slug"], day),
                title_ru=str(meta["title_ru"]),
                country=str(meta["country"]),
                category=str(meta["category"]),
                importance=str(meta["importance"]),
                scheduled_at_msk=msk_datetime(day, int(meta["hour"]), int(meta["minute"])),
                source=str(meta["source"]),
                linked_indicator_id=str(meta["linked_indicator_id"]),
                unit=str(meta["unit"]),
            )
        )
    return drafts


def _parse_fomc_dates(text: str, date_from: date, date_to: date) -> set[date]:
    found: set[date] = set()
    for match in _DATE_RE.finditer(text):
        month = _MONTHS.get(match.group(1).lower())
        if month is None:
            continue
        day = int(match.group(2))
        year = int(match.group(3))
        try:
            parsed = date(year, month, day)
        except ValueError:
            continue
        if date_from <= parsed <= date_to:
            found.add(parsed)
    return found
