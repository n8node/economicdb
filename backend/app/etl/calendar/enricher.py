from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.calendar.writer import update_event_values
from app.models.events import EconomicEvent
from app.models.indicators import IndicatorValue


async def enrich_past_events(
    session: AsyncSession,
    *,
    dry_run: bool = False,
    limit: int = 500,
) -> dict:
    now = datetime.now(timezone.utc)
    rows = await session.scalars(
        select(EconomicEvent)
        .where(EconomicEvent.scheduled_at_msk <= now)
        .where(EconomicEvent.linked_indicator_id.is_not(None))
        .order_by(EconomicEvent.scheduled_at_msk.desc())
        .limit(limit)
    )
    enriched = 0
    skipped = 0

    for event in rows.all():
        indicator_id = event.linked_indicator_id
        if not indicator_id:
            skipped += 1
            continue

        event_day = event.scheduled_at_msk.date()
        window_start = event_day - timedelta(days=45)
        window_end = event_day + timedelta(days=7)

        values = await session.execute(
            select(IndicatorValue.observed_at, IndicatorValue.value)
            .where(IndicatorValue.indicator_id == indicator_id)
            .where(IndicatorValue.observed_at >= window_start)
            .where(IndicatorValue.observed_at <= window_end)
            .order_by(IndicatorValue.observed_at)
        )
        points = [(observed_at, value) for observed_at, value in values.all()]
        if not points:
            skipped += 1
            continue

        actual_point = _pick_actual_point(points, event_day)
        if actual_point is None:
            skipped += 1
            continue

        actual_date, actual_value = actual_point
        previous_value = _pick_previous(points, actual_date)
        surprise = None
        if event.forecast is not None:
            surprise = actual_value - event.forecast

        changed = (
            event.actual != actual_value
            or (previous_value is not None and event.previous != previous_value)
            or (surprise is not None and event.surprise != surprise)
        )
        if not changed:
            continue

        await update_event_values(
            session,
            event.id,
            actual=actual_value,
            previous=previous_value,
            surprise=surprise,
            dry_run=dry_run,
        )
        enriched += 1

    if not dry_run and enriched:
        await session.flush()

    return {"enriched": enriched, "skipped": skipped}


def _pick_actual_point(
    points: list[tuple[object, Decimal]],
    event_day: object,
) -> tuple[object, Decimal] | None:
    on_or_after = [(d, v) for d, v in points if d >= event_day]
    if on_or_after:
        return on_or_after[0]
    return points[-1]


def _pick_previous(points: list[tuple[object, Decimal]], actual_date: object) -> Decimal | None:
    prior = [(d, v) for d, v in points if d < actual_date]
    if not prior:
        return None
    return prior[-1][1]
