from __future__ import annotations

import re
from datetime import date

import httpx

from app.etl.calendar.mappings import TIER_A_EVENTS, event_id, msk_datetime
from app.etl.calendar.writer import CalendarEventDraft

ECB_CALENDAR_URL = "https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html"
ECB_ICAL_URL = "https://www.ecb.europa.eu/press/calendars/mgcgc/mgcgc.ics"

_DATE_RE = re.compile(r"(\d{4})(\d{2})(\d{2})")
_ICAL_DATE_RE = re.compile(r"DTSTART(?:;VALUE=DATE)?:(\d{8})")


async def fetch_ecb_calendar_events(*, date_from: date, date_to: date) -> list[CalendarEventDraft]:
    meta = TIER_A_EVENTS["ecb"]
    meeting_days: set[date] = set()

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for url in (ECB_ICAL_URL, ECB_CALENDAR_URL):
            try:
                response = await client.get(url, headers={"User-Agent": "economicdb-calendar/1.0"})
                response.raise_for_status()
                meeting_days.update(_parse_ecb_dates(response.text, date_from, date_to))
            except httpx.HTTPError:
                continue

    drafts: list[CalendarEventDraft] = []
    for day in sorted(meeting_days):
        drafts.append(
            CalendarEventDraft(
                id=event_id("ecb", meta["slug"], day),
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


def _parse_ecb_dates(text: str, date_from: date, date_to: date) -> set[date]:
    found: set[date] = set()
    for match in _ICAL_DATE_RE.finditer(text):
        parsed = _iso_date(match.group(1))
        if parsed and date_from <= parsed <= date_to:
            found.add(parsed)
    if found:
        return found

    for match in _DATE_RE.finditer(text):
        parsed = _iso_date(match.group(0))
        if parsed and date_from <= parsed <= date_to:
            found.add(parsed)
    return found


def _iso_date(raw: str) -> date | None:
    if len(raw) != 8:
        return None
    try:
        return date(int(raw[0:4]), int(raw[4:6]), int(raw[6:8]))
    except ValueError:
        return None
