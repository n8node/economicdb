from __future__ import annotations

import statistics
from datetime import date
from decimal import Decimal

from app.analytics.series import compute_change, delta_direction


def _months_diff(a: date, b: date) -> int:
    return (a.year - b.year) * 12 + (a.month - b.month)


def _find_lagged(points: list[tuple[date, float]], lag_months: int) -> float | None:
    if len(points) < 2:
        return None
    last_date, _ = points[-1]
    for observed, value in reversed(points[:-1]):
        if _months_diff(last_date, observed) == lag_months:
            return value
    return None


def _period_lag(frequency: str) -> int | None:
    if frequency == "monthly":
        return 1
    if frequency == "quarterly":
        return 3
    if frequency == "yearly" or frequency == "annual":
        return 12
    return None


def _streak(values: list[float]) -> tuple[int, str]:
    if len(values) < 2:
        return 0, "flat"
    direction = "flat"
    streak = 0
    for idx in range(len(values) - 1, 0, -1):
        diff = values[idx] - values[idx - 1]
        if diff == 0:
            break
        step = "up" if diff > 0 else "down"
        if direction == "flat":
            direction = step
            streak = 1
        elif step == direction:
            streak += 1
        else:
            break
    return streak, direction


def compute_indicator_stats(
    points: list[tuple[date, Decimal | float]],
    *,
    unit: str | None,
    frequency: str,
) -> dict | None:
    if not points:
        return None

    normalized: list[tuple[date, float]] = [(obs, float(val)) for obs, val in points]
    values = [v for _, v in normalized]
    first_date, first_value = normalized[0]
    last_date, last_value = normalized[-1]

    min_idx = min(range(len(values)), key=lambda i: values[i])
    max_idx = max(range(len(values)), key=lambda i: values[i])
    avg = sum(values) / len(values)
    median = statistics.median(values)
    change = last_value - first_value
    change_pct = None if first_value == 0 else (change / abs(first_value)) * 100

    cagr = None
    years = (last_date - first_date).days / 365.25
    if years >= 1 and first_value > 0 and last_value > 0:
        cagr = ((last_value / first_value) ** (1 / years) - 1) * 100

    volatility = statistics.pstdev(values) if len(values) > 1 else 0.0
    above_current = sum(1 for v in values if v > last_value)
    pct_above_current = round(above_current / len(values) * 100, 1)

    lag = _period_lag(frequency)
    mom_qoq = None
    yoy = None
    if lag == 1:
        prev = _find_lagged(normalized, 1)
        if prev is not None:
            mom_qoq = float(compute_change(Decimal(str(last_value)), Decimal(str(prev)), unit) or 0)
        prev_y = _find_lagged(normalized, 12)
        if prev_y is not None:
            yoy = float(compute_change(Decimal(str(last_value)), Decimal(str(prev_y)), unit) or 0)
    elif lag == 3:
        prev = _find_lagged(normalized, 3)
        if prev is not None:
            mom_qoq = float(compute_change(Decimal(str(last_value)), Decimal(str(prev)), unit) or 0)
        prev_y = _find_lagged(normalized, 12)
        if prev_y is not None:
            yoy = float(compute_change(Decimal(str(last_value)), Decimal(str(prev_y)), unit) or 0)
    elif lag == 12:
        prev = _find_lagged(normalized, 12)
        if prev is not None:
            yoy = float(compute_change(Decimal(str(last_value)), Decimal(str(prev)), unit) or 0)

    streak, streak_direction = _streak(values)

    return {
        "min": values[min_idx],
        "max": values[max_idx],
        "avg": avg,
        "median": median,
        "change": change,
        "change_pct": change_pct,
        "cagr": cagr,
        "volatility": volatility,
        "pct_above_current": pct_above_current,
        "best": {"date": normalized[max_idx][0], "value": values[max_idx]},
        "worst": {"date": normalized[min_idx][0], "value": values[min_idx]},
        "last_observed_at": last_date,
        "mom_qoq": mom_qoq,
        "yoy": yoy,
        "streak": streak,
        "streak_direction": streak_direction,
        "change_direction": delta_direction(Decimal(str(change))),
    }
