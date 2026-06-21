from __future__ import annotations

import re
from datetime import date

NUMBER_PATTERN = re.compile(r"-?\d+[,.]?\d*")


def numbers_from_text(text: str) -> set[float]:
    values: set[float] = set()
    for match in NUMBER_PATTERN.finditer(text):
        raw = match.group(0).replace(",", ".")
        try:
            values.add(round(float(raw), 4))
        except ValueError:
            continue
    return values


def numeric_variants(value: float) -> set[float]:
    if value != value:  # NaN
        return set()
    variants = {
        value,
        round(value, 4),
        round(value, 3),
        round(value, 2),
        round(value, 1),
        abs(value),
        -abs(value),
    }
    if abs(value - round(value)) <= 0.05:
        variants.add(float(int(round(value))))
    return {round(item, 4) for item in variants}


def expand_numeric_variants(values: set[float]) -> set[float]:
    expanded: set[float] = set()
    for value in values:
        expanded |= numeric_variants(value)
    return expanded


def period_benign_numbers(period_start: date, period_end: date) -> set[float]:
    benign: set[float] = set()
    for day in (period_start, period_end):
        benign.add(float(day.day))
        benign.add(float(day.month))
        benign.add(float(day.year))
    for year in range(period_start.year - 1, period_end.year + 2):
        benign.add(float(year))
    for day in range(1, 32):
        benign.add(float(day))
    return benign


def matches_allowed_number(value: float, allowed: set[float]) -> bool:
    if value in allowed:
        return True

    for candidate in allowed:
        if abs(candidate - value) <= 0.25:
            return True
        if candidate != 0 and abs((candidate - value) / candidate) <= 0.025:
            return True
        if abs(round(candidate) - value) <= 0.05:
            return True
        if abs(round(candidate, 1) - value) <= 0.05:
            return True

    return False
