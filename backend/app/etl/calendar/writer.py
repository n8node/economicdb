from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.events import EconomicEvent


@dataclass
class CalendarEventDraft:
    id: str
    title_ru: str
    country: str
    category: str
    importance: str
    scheduled_at_msk: datetime
    source: str
    linked_indicator_id: str | None = None
    unit: str | None = None


async def upsert_events(
    session: AsyncSession,
    drafts: list[CalendarEventDraft],
    *,
    dry_run: bool = False,
) -> tuple[int, list[str]]:
    if not drafts:
        return 0, []

    ids = [draft.id for draft in drafts]
    existing_rows = await session.scalars(select(EconomicEvent).where(EconomicEvent.id.in_(ids)))
    existing = {row.id: row for row in existing_rows.all()}

    upserted: list[str] = []
    for draft in drafts:
        row = existing.get(draft.id)
        if row is None:
            row = EconomicEvent(
                id=draft.id,
                title_ru=draft.title_ru,
                country=draft.country,
                category=draft.category,
                importance=draft.importance,
                scheduled_at_msk=draft.scheduled_at_msk,
                source=draft.source,
                linked_indicator_id=draft.linked_indicator_id,
                unit=draft.unit,
            )
            if not dry_run:
                session.add(row)
            upserted.append(draft.id)
            continue

        changed = False
        for field, value in (
            ("title_ru", draft.title_ru),
            ("country", draft.country),
            ("category", draft.category),
            ("importance", draft.importance),
            ("scheduled_at_msk", draft.scheduled_at_msk),
            ("source", draft.source),
            ("linked_indicator_id", draft.linked_indicator_id),
            ("unit", draft.unit),
        ):
            if getattr(row, field) != value:
                setattr(row, field, value)
                changed = True
        if changed:
            upserted.append(draft.id)

    if not dry_run and upserted:
        await session.flush()

    return len(upserted), upserted


async def update_event_values(
    session: AsyncSession,
    event_id: str,
    *,
    actual: Decimal | None = None,
    previous: Decimal | None = None,
    forecast: Decimal | None = None,
    surprise: Decimal | None = None,
    dry_run: bool = False,
) -> bool:
    row = await session.get(EconomicEvent, event_id)
    if row is None:
        return False
    if dry_run:
        return True
    if actual is not None:
        row.actual = actual
    if previous is not None:
        row.previous = previous
    if forecast is not None:
        row.forecast = forecast
    if surprise is not None:
        row.surprise = surprise
    return True
