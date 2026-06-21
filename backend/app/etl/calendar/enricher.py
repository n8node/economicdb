from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.calendar.values import (
    event_day_msk,
    load_indicator_points,
    merge_event_values,
    resolve_event_values,
    value_window,
)
from app.etl.calendar.writer import update_event_values
from app.models.events import EconomicEvent


async def enrich_past_events(
    session: AsyncSession,
    *,
    dry_run: bool = False,
    batch_size: int = 500,
) -> dict:
    now = datetime.now(timezone.utc)
    enriched = 0
    skipped = 0
    offset = 0

    while True:
        rows = await session.scalars(
            select(EconomicEvent)
            .where(EconomicEvent.scheduled_at_msk <= now)
            .where(EconomicEvent.linked_indicator_id.is_not(None))
            .order_by(EconomicEvent.scheduled_at_msk.desc())
            .offset(offset)
            .limit(batch_size)
        )
        batch = rows.all()
        if not batch:
            break

        for event in batch:
            indicator_id = event.linked_indicator_id
            if not indicator_id:
                skipped += 1
                continue

            window_start, window_end = value_window(event_day_msk(event))
            points = await load_indicator_points(
                session,
                indicator_id,
                window_start=window_start,
                window_end=window_end,
            )
            resolved = resolve_event_values(event, points)
            if resolved is None:
                skipped += 1
                continue

            actual, previous, surprise = merge_event_values(event, resolved)
            if actual is None and previous is None:
                skipped += 1
                continue

            changed = (
                (actual is not None and event.actual != actual)
                or (previous is not None and event.previous != previous)
                or (surprise is not None and event.surprise != surprise)
            )
            if not changed:
                continue

            await update_event_values(
                session,
                event.id,
                actual=actual,
                previous=previous,
                surprise=surprise,
                dry_run=dry_run,
            )
            enriched += 1

        offset += batch_size

    if not dry_run and enriched:
        await session.flush()

    return {"enriched": enriched, "skipped": skipped}
