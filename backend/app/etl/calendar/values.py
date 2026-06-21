from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezones import MSK
from app.models.events import EconomicEvent
from app.models.indicators import IndicatorValue

RATE_INDICATOR_IDS = frozenset({"cbr_key_rate", "fed_funds", "ecb_deposit_rate"})
LOOKBACK_DAYS = 450
LOOKAHEAD_DAYS = 14


@dataclass(frozen=True)
class ResolvedEventValues:
    actual: Decimal | None = None
    previous: Decimal | None = None
    surprise: Decimal | None = None


def event_day_msk(event: EconomicEvent) -> date:
    return event.scheduled_at_msk.astimezone(MSK).date()


def value_window(event_day: date) -> tuple[date, date]:
    return event_day - timedelta(days=LOOKBACK_DAYS), event_day + timedelta(days=LOOKAHEAD_DAYS)


def resolve_event_values(
    event: EconomicEvent,
    points: list[tuple[date, Decimal]],
) -> ResolvedEventValues | None:
    if not points:
        return None

    event_day = event_day_msk(event)
    indicator_id = event.linked_indicator_id or ""
    if indicator_id in RATE_INDICATOR_IDS:
        resolved = _pick_rate_decision(points, event_day)
    else:
        resolved = _pick_release_values(points, event_day)

    if resolved is None:
        return None

    actual, previous = resolved
    surprise = None
    if event.forecast is not None:
        surprise = actual - event.forecast
    return ResolvedEventValues(actual=actual, previous=previous, surprise=surprise)


def merge_event_values(
    event: EconomicEvent,
    resolved: ResolvedEventValues | None,
) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
    if resolved is not None:
        actual = resolved.actual
        previous = resolved.previous
        surprise = resolved.surprise
        if surprise is None and actual is not None and event.forecast is not None:
            surprise = actual - event.forecast
        return actual, previous, surprise

    return event.actual, event.previous, event.surprise


async def load_indicator_points(
    session: AsyncSession,
    indicator_id: str,
    *,
    window_start: date,
    window_end: date,
) -> list[tuple[date, Decimal]]:
    rows = await session.execute(
        select(IndicatorValue.observed_at, IndicatorValue.value)
        .where(IndicatorValue.indicator_id == indicator_id)
        .where(IndicatorValue.observed_at >= window_start)
        .where(IndicatorValue.observed_at <= window_end)
        .order_by(IndicatorValue.observed_at)
    )
    return [(observed_at, value) for observed_at, value in rows.all()]


async def resolve_events_values(
    session: AsyncSession,
    events: list[EconomicEvent],
    *,
    now: datetime | None = None,
) -> dict[str, ResolvedEventValues]:
    current = now or datetime.now(timezone.utc)
    pending = [
        event
        for event in events
        if event.linked_indicator_id and event.scheduled_at_msk <= current
    ]
    if not pending:
        return {}

    grouped: dict[str, list[EconomicEvent]] = {}
    for event in pending:
        grouped.setdefault(event.linked_indicator_id or "", []).append(event)

    resolved_by_id: dict[str, ResolvedEventValues] = {}
    for indicator_id, indicator_events in grouped.items():
        if not indicator_id:
            continue

        window_start = min(value_window(event_day_msk(event))[0] for event in indicator_events)
        window_end = max(value_window(event_day_msk(event))[1] for event in indicator_events)
        points = await load_indicator_points(
            session,
            indicator_id,
            window_start=window_start,
            window_end=window_end,
        )
        for event in indicator_events:
            resolved = resolve_event_values(event, points)
            if resolved is not None:
                resolved_by_id[event.id] = resolved

    return resolved_by_id


def _pick_release_values(
    points: list[tuple[date, Decimal]],
    event_day: date,
) -> tuple[Decimal, Decimal | None] | None:
    publication_month = _publication_month_start(event_day)
    publication_points = [(d, v) for d, v in points if d == publication_month]
    if publication_points:
        actual_date, actual_value = publication_points[-1]
        return actual_value, _pick_previous(points, actual_date)

    same_month = [(d, v) for d, v in points if d.year == event_day.year and d.month == event_day.month]
    if same_month:
        actual_date, actual_value = same_month[-1]
        return actual_value, _pick_previous(points, actual_date)

    on_or_before = [(d, v) for d, v in points if d <= event_day]
    if on_or_before:
        actual_date, actual_value = on_or_before[-1]
        return actual_value, _pick_previous(points, actual_date)

    actual_date, actual_value = points[-1]
    return actual_value, _pick_previous(points, actual_date)


def _publication_month_start(event_day: date) -> date:
    if event_day.month == 1:
        return date(event_day.year - 1, 12, 1)
    return date(event_day.year, event_day.month - 1, 1)


def _pick_rate_decision(
    points: list[tuple[date, Decimal]],
    event_day: date,
) -> tuple[Decimal, Decimal | None] | None:
    deadline = event_day + timedelta(days=3)
    for observed_at, value in points:
        if observed_at < event_day or observed_at > deadline:
            continue
        previous_value = _pick_previous(points, observed_at)
        if previous_value is not None and previous_value != value:
            return value, previous_value

    on_day = [(d, v) for d, v in points if d == event_day]
    if on_day:
        actual_value = on_day[0][1]
        return actual_value, _pick_previous(points, event_day)

    on_or_after = [(d, v) for d, v in points if d >= event_day]
    if on_or_after:
        actual_date, actual_value = on_or_after[0]
        return actual_value, _pick_previous(points, actual_date)

    actual_date, actual_value = points[-1]
    return actual_value, _pick_previous(points, actual_date)


def _pick_previous(points: list[tuple[date, Decimal]], actual_date: date) -> Decimal | None:
    prior = [(d, v) for d, v in points if d < actual_date]
    if not prior:
        return None
    return prior[-1][1]
