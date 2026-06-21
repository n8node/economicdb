from __future__ import annotations

import re
from datetime import date

import httpx

from app.etl.calendar.mappings import TIER_A_EVENTS, event_id, msk_datetime
from app.etl.calendar.writer import CalendarEventDraft

CBR_PLAN_URL = "https://www.cbr.ru/development/sc_plan/"
CBR_KEY_RATE_URL = "https://www.cbr.ru/hd_base/KeyRate/"

_DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")


async def fetch_cbr_calendar_events(*, date_from: date, date_to: date) -> list[CalendarEventDraft]:
    meta = TIER_A_EVENTS["cbr"]
    meeting_days: set[date] = set()

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for url in (CBR_PLAN_URL, CBR_KEY_RATE_URL):
            try:
                response = await client.get(url, headers={"User-Agent": "economicdb-calendar/1.0"})
                response.raise_for_status()
                meeting_days.update(_parse_russian_dates(response.text, date_from, date_to))
            except httpx.HTTPError:
                continue

    drafts: list[CalendarEventDraft] = []
    for day in sorted(meeting_days):
        drafts.append(
            CalendarEventDraft(
                id=event_id("cbr", meta["slug"], day),
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


def _parse_russian_dates(text: str, date_from: date, date_to: date) -> set[date]:
    found: set[date] = set()
    for match in _DATE_RE.finditer(text):
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))
        try:
            parsed = date(year, month, day)
        except ValueError:
            continue
        if date_from <= parsed <= date_to:
            found.add(parsed)
    return found
