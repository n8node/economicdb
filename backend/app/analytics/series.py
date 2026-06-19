from __future__ import annotations

from datetime import date
from decimal import Decimal


def decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def delta_direction(change: Decimal | None) -> str:
    if change is None or change == 0:
        return "flat"
    return "up" if change > 0 else "down"


def format_value(value: Decimal | None, unit: str | None) -> str | None:
    if value is None:
        return None
    num = float(value)
    if unit == "%":
        return f"{num:.2f}%".replace(".", ",")
    if unit == "п.п.":
        signed = f"+{num:.2f}" if num > 0 else f"{num:.2f}"
        return f"{signed.replace('.', ',')} п.п."
    if unit in {"RUB", "USD", "EUR", "index"}:
        return f"{num:,.2f}".replace(",", " ").replace(".", ",")
    if unit == "mln":
        return f"{num:,.1f} млн".replace(",", " ").replace(".", ",")
    return f"{num:.2f}".replace(".", ",")


def format_change(change: Decimal | None, unit: str | None) -> str | None:
    if change is None:
        return None
    num = float(change)
    if unit == "%" or unit == "п.п.":
        suffix = " п.п." if unit == "п.п." else "%"
        signed = f"+{num:.2f}" if num > 0 else f"{num:.2f}"
        return f"{signed.replace('.', ',')}{suffix}"
    if num > 0:
        return f"+{num:.2f}%".replace(".", ",")
    return f"{num:.2f}%".replace(".", ",")


def compute_change(current: Decimal | None, previous: Decimal | None, unit: str | None) -> Decimal | None:
    if current is None or previous is None:
        return None
    if unit == "%" or unit == "п.п.":
        return current - previous
    if previous == 0:
        return None
    pct = (current - previous) / abs(previous) * 100
    return Decimal(str(round(float(pct), 2)))


def sparkline_values(points: list[tuple[date, Decimal]], limit: int = 12) -> list[float]:
    tail = points[-limit:]
    return [float(p[1]) for p in tail]
