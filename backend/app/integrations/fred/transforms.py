from __future__ import annotations

from datetime import date
from decimal import Decimal


def apply_transform(
    transform: str,
    observations: list[tuple[date, Decimal]],
) -> list[tuple[date, Decimal]]:
    if transform == "direct":
        return observations
    if transform == "yoy_percent":
        return _yoy_percent(observations)
    if transform == "mom_diff":
        return _mom_diff(observations)
    return observations


def _prev_year_month(d: date) -> date:
    return date(d.year - 1, d.month, 1)


def _yoy_percent(observations: list[tuple[date, Decimal]]) -> list[tuple[date, Decimal]]:
    by_date = {d: v for d, v in observations}
    result: list[tuple[date, Decimal]] = []
    for observed, value in observations:
        prev = _prev_year_month(observed)
        prev_value = by_date.get(prev)
        if prev_value is None or prev_value == 0:
            continue
        yoy = (value / prev_value - Decimal("1")) * Decimal("100")
        result.append((observed, yoy.quantize(Decimal("0.01"))))
    return result


def _mom_diff(observations: list[tuple[date, Decimal]]) -> list[tuple[date, Decimal]]:
    if len(observations) < 2:
        return []
    result: list[tuple[date, Decimal]] = []
    prev_value = observations[0][1]
    for observed, value in observations[1:]:
        diff = value - prev_value
        result.append((observed, diff.quantize(Decimal("0.1"))))
        prev_value = value
    return result


def compute_last_change(values: list[tuple[date, Decimal]], unit: str | None) -> Decimal:
    if len(values) < 2:
        return Decimal("0")
    last_val = values[-1][1]
    prev_val = values[-2][1]
    if unit in {"%", "п.п.", "index", "RUB", "USD"}:
        change = last_val - prev_val
    else:
        change = (last_val - prev_val) / abs(prev_val) * Decimal("100") if prev_val else Decimal("0")
    return Decimal(str(round(float(change), 2)))
