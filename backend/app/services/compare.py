from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.series import delta_direction, format_change, format_value
from app.models.indicators import Indicator, IndicatorValue
from app.schemas.compare import ComparePreset, CompareSeriesItem, CompareSeriesRequest, CompareSeriesResponse, CompareSeriesStats


def _month_grid(date_from: date | None, date_to: date) -> list[date]:
    if date_from is None:
        date_from = date_to - timedelta(days=365 * 2)
    points: list[date] = []
    y, m = date_from.year, date_from.month
    while date(y, m, 1) <= date(date_to.year, date_to.month, 1):
        points.append(date(y, m, 1))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return points or [date_to.replace(day=1)]


def _locf(values: dict[date, Decimal], grid: list[date]) -> list[float | None]:
    result: list[float | None] = []
    last: float | None = None
    for point in grid:
        if point in values:
            last = float(values[point])
        elif any(d <= point for d in values):
            nearest = max(d for d in values if d <= point)
            last = float(values[nearest])
        result.append(last)
    return result


def _normalize(values: list[float | None], mode: str) -> list[float | None]:
    if mode == "absolute":
        return values
    clean = [v for v in values if v is not None]
    if not clean:
        return values
    if mode == "index":
        base = clean[0]
        if base == 0:
            return values
        return [None if v is None else round(v / base * 100, 4) for v in values]
    if mode == "change":
        base = clean[0]
        if base == 0:
            return values
        return [None if v is None else round((v - base) / abs(base) * 100, 4) for v in values]
    return values


def _stats(values: list[float | None]) -> CompareSeriesStats:
    clean = [v for v in values if v is not None]
    if not clean:
        return CompareSeriesStats(min=0, max=0, avg=0, change=0, change_direction="flat")
    change = clean[-1] - clean[0]
    return CompareSeriesStats(
        min=round(min(clean), 4),
        max=round(max(clean), 4),
        avg=round(sum(clean) / len(clean), 4),
        change=round(change, 4),
        change_direction=delta_direction(Decimal(str(change))),
    )


async def build_compare_series(session: AsyncSession, req: CompareSeriesRequest) -> CompareSeriesResponse:
    date_to = req.date_to or date.today()
    date_from = req.date_from or (date_to - timedelta(days=365))
    grid = _month_grid(date_from, date_to)
    labels = [d.strftime("%Y-%m") for d in grid]

    indicators = (
        await session.scalars(
            select(Indicator).where(
                Indicator.id.in_(req.indicator_ids),
                Indicator.enabled.is_(True),
            )
        )
    ).all()
    indicator_map = {i.id: i for i in indicators}

    series_items: list[CompareSeriesItem] = []
    units: set[str] = set()

    for indicator_id in req.indicator_ids:
        indicator = indicator_map.get(indicator_id)
        if indicator is None:
            continue
        rows = await session.execute(
            select(IndicatorValue.observed_at, IndicatorValue.value)
            .where(IndicatorValue.indicator_id == indicator_id)
            .where(IndicatorValue.observed_at <= date_to)
            .where(IndicatorValue.observed_at >= date_from)
            .order_by(IndicatorValue.observed_at)
        )
        value_map = {obs: val for obs, val in rows.all()}
        aligned = _locf(value_map, grid)
        normalized = _normalize(aligned, req.normalize)
        stats = _stats(normalized)
        if indicator.unit:
            units.add(indicator.unit)
        series_items.append(
            CompareSeriesItem(
                indicator_id=indicator.id,
                name_ru=indicator.name_ru,
                country=indicator.country,
                source=indicator.source,
                unit=indicator.unit,
                values=normalized,
                last_value=format_value(indicator.last_value, indicator.unit),
                last_change=format_change(indicator.last_change, indicator.unit if indicator.unit in {"%", "п.п."} else "%"),
                delta_direction=delta_direction(indicator.last_change),
                stats=stats,
            )
        )

    unit_warning = len(units) > 1 and req.normalize == "absolute"
    axis_notes = {
        "absolute": "Ось Y: абсолютные значения",
        "index": "Ось Y: индекс (100 = начало периода)",
        "change": "Ось Y: изменение от начала периода, %",
    }

    return CompareSeriesResponse(
        labels=labels,
        dates=grid,
        series=series_items,
        unit_warning=unit_warning,
        axis_note=axis_notes[req.normalize],
        normalize=req.normalize,
    )


def list_presets() -> list[ComparePreset]:
    from app.data.compare_presets import COMPARE_PRESETS

    return [
        ComparePreset(key=key, label=data["label"], indicator_ids=data["indicator_ids"])
        for key, data in COMPARE_PRESETS.items()
    ]
