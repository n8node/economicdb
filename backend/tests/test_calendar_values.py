from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from app.core.timezones import MSK
from app.etl.calendar.values import _pick_rate_decision, _pick_release_values, resolve_event_values
from app.models.events import EconomicEvent


def _event(indicator_id: str, day: date) -> EconomicEvent:
    return EconomicEvent(
        id=f"test:{indicator_id}:{day.isoformat()}",
        title_ru="Test",
        country="ru",
        category="rates",
        importance="high",
        scheduled_at_msk=datetime.combine(day, datetime.min.time(), tzinfo=MSK),
        source="cbr",
        linked_indicator_id=indicator_id,
        unit="%",
    )


def test_release_values_use_publication_month() -> None:
    event_day = date(2025, 5, 13)
    points = [
        (date(2025, 4, 1), Decimal("2.33")),
        (date(2025, 5, 1), Decimal("2.38")),
    ]

    actual, previous = _pick_release_values(points, event_day)

    assert actual == Decimal("2.38")
    assert previous == Decimal("2.33")


def test_rate_decision_uses_change_on_meeting_day() -> None:
    event_day = date(2025, 2, 14)
    points = [
        (date(2025, 2, 13), Decimal("21.00")),
        (date(2025, 2, 14), Decimal("21.00")),
        (date(2025, 2, 17), Decimal("21.00")),
    ]

    actual, previous = _pick_rate_decision(points, event_day)

    assert actual == Decimal("21.00")
    assert previous == Decimal("21.00")


def test_rate_decision_detects_new_rate() -> None:
    event_day = date(2024, 12, 20)
    points = [
        (date(2024, 12, 19), Decimal("21.00")),
        (date(2024, 12, 20), Decimal("21.00")),
        (date(2024, 12, 21), Decimal("21.00")),
        (date(2024, 12, 22), Decimal("18.00")),
    ]

    actual, previous = _pick_rate_decision(points, event_day)

    assert actual == Decimal("18.00")
    assert previous == Decimal("21.00")


def test_resolve_event_values_returns_none_without_points() -> None:
    event = _event("us_cpi_yoy", date(2025, 5, 13))
    assert resolve_event_values(event, []) is None
