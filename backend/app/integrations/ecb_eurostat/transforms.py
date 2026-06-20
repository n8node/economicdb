from __future__ import annotations

from datetime import date
from decimal import Decimal


def _prev_year_period(observed: date, *, quarterly: bool) -> date:
    if quarterly:
        return date(observed.year - 1, observed.month, 1)
    return date(observed.year - 1, observed.month, 1)


def yoy_percent_from_index(
    observations: list[tuple[date, Decimal]],
    *,
    quarterly: bool = False,
) -> list[tuple[date, Decimal]]:
    by_date = {d: v for d, v in observations}
    result: list[tuple[date, Decimal]] = []
    for observed, value in observations:
        prev = _prev_year_period(observed, quarterly=quarterly)
        prev_value = by_date.get(prev)
        if prev_value is None or prev_value == 0:
            continue
        yoy = (value / prev_value - Decimal("1")) * Decimal("100")
        result.append((observed, yoy.quantize(Decimal("0.01"))))
    return result


def external_id_needs_index_yoy(external_id: str) -> bool:
    key = external_id.split("/", 1)[-1]
    parts = key.split(".")
    return any(part in {"I21", "I15", "I10"} for part in parts)
