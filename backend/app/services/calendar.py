from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.events import EconomicEvent
from app.schemas.calendar import CalendarEventDetail, CalendarEventItem, CalendarEventsResponse, CalendarSurpriseItem

MSK = ZoneInfo("Europe/Moscow")


def _format_num(value, unit: str | None) -> str | None:
    if value is None:
        return None
    num = float(value)
    if unit == "%":
        return f"{num:.2f}%".replace(".", ",")
    if unit == "k":
        return f"{num:.0f}k"
    return f"{num:.2f}".replace(".", ",")


def _format_dt(dt: datetime) -> str:
    local = dt.astimezone(MSK)
    return local.strftime("%d.%m.%Y, %H:%M МСК")


def _surprise_direction(surprise) -> str | None:
    if surprise is None:
        return None
    val = float(surprise)
    if val == 0:
        return "flat"
    return "up" if val > 0 else "down"


def _to_item(row: EconomicEvent, now: datetime) -> CalendarEventItem:
    status = "upcoming" if row.scheduled_at_msk > now else "past"
    return CalendarEventItem(
        id=row.id,
        title_ru=row.title_ru,
        country=row.country,
        category=row.category,
        importance=row.importance,
        scheduled_at_msk=row.scheduled_at_msk,
        scheduled_label=_format_dt(row.scheduled_at_msk),
        status=status,
        actual=_format_num(row.actual, row.unit),
        forecast=_format_num(row.forecast, row.unit) if row.forecast is not None else "—",
        previous=_format_num(row.previous, row.unit),
        surprise=_format_num(row.surprise, row.unit),
        surprise_direction=_surprise_direction(row.surprise),
        source=row.source,
        linked_indicator_id=row.linked_indicator_id,
    )


async def list_events(
    session: AsyncSession,
    *,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    country: list[str] | None = None,
    importance: list[str] | None = None,
    category: list[str] | None = None,
    status: str | None = None,
) -> CalendarEventsResponse:
    now = datetime.now(timezone.utc)
    query = select(EconomicEvent)
    clauses = []
    if date_from:
        clauses.append(EconomicEvent.scheduled_at_msk >= date_from)
    if date_to:
        clauses.append(EconomicEvent.scheduled_at_msk <= date_to)
    if country:
        clauses.append(EconomicEvent.country.in_(country))
    if importance:
        clauses.append(EconomicEvent.importance.in_(importance))
    if category:
        clauses.append(EconomicEvent.category.in_(category))
    if clauses:
        query = query.where(and_(*clauses))

    rows = list((await session.scalars(query.order_by(EconomicEvent.scheduled_at_msk))).all())
    items = [_to_item(row, now) for row in rows]
    if status == "upcoming":
        items = [i for i in items if i.status == "upcoming"]
    elif status == "past":
        items = [i for i in items if i.status == "past"]
    return CalendarEventsResponse(items=items, total=len(items))


async def get_event(session: AsyncSession, event_id: str) -> CalendarEventDetail | None:
    row = await session.get(EconomicEvent, event_id)
    if row is None:
        return None
    now = datetime.now(timezone.utc)
    item = _to_item(row, now)
    return CalendarEventDetail(**item.model_dump(), unit=row.unit)


async def recent_surprises(session: AsyncSession, limit: int = 5) -> list[CalendarSurpriseItem]:
    rows = await session.scalars(
        select(EconomicEvent)
        .where(EconomicEvent.surprise.is_not(None))
        .order_by(EconomicEvent.scheduled_at_msk.desc())
        .limit(limit)
    )
    result: list[CalendarSurpriseItem] = []
    for row in rows.all():
        direction = _surprise_direction(row.surprise) or "flat"
        result.append(
            CalendarSurpriseItem(
                id=row.id,
                title_ru=row.title_ru,
                surprise=_format_num(row.surprise, row.unit) or "—",
                surprise_direction=direction,
                scheduled_label=_format_dt(row.scheduled_at_msk),
            )
        )
    return result
