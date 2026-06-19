from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.indicators import get_db
from app.schemas.calendar import CalendarEventDetail, CalendarEventsResponse, CalendarSurpriseItem
from app.services import calendar as calendar_service

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events", response_model=CalendarEventsResponse)
async def calendar_events(
    date_from: datetime | None = Query(default=None, alias="from"),
    date_to: datetime | None = Query(default=None, alias="to"),
    country: list[str] = Query(default=[]),
    importance: list[str] = Query(default=[]),
    category: list[str] = Query(default=[]),
    status: str | None = Query(default=None, pattern="^(upcoming|past)$"),
    session: AsyncSession = Depends(get_db),
) -> CalendarEventsResponse:
    return await calendar_service.list_events(
        session,
        date_from=date_from,
        date_to=date_to,
        country=country or None,
        importance=importance or None,
        category=category or None,
        status=status,
    )


@router.get("/events/{event_id}", response_model=CalendarEventDetail)
async def calendar_event(event_id: str, session: AsyncSession = Depends(get_db)) -> CalendarEventDetail:
    item = await calendar_service.get_event(session, event_id)
    if item is None:
        raise HTTPException(status_code=404, detail="event_not_found")
    return item


@router.get("/surprises", response_model=list[CalendarSurpriseItem])
async def calendar_surprises(
    limit: int = Query(default=5, ge=1, le=20),
    session: AsyncSession = Depends(get_db),
) -> list[CalendarSurpriseItem]:
    return await calendar_service.recent_surprises(session, limit)


@router.get("/export.ics")
async def calendar_export_ics(session: AsyncSession = Depends(get_db)) -> Response:
    data = await calendar_service.list_events(session)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//economicdb//Macro//RU"]
    for event in data.items:
        dt = event.scheduled_at_msk.strftime("%Y%m%dT%H%M%SZ")
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{event.id}@economicdb.com",
                f"DTSTART:{dt}",
                f"SUMMARY:{event.title_ru}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    body = "\r\n".join(lines)
    return Response(content=body, media_type="text/calendar; charset=utf-8")
