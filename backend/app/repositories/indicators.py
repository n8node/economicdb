from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.series import (
    delta_direction,
    format_change,
    format_value,
    sparkline_values,
)
from app.models.indicators import Indicator, IndicatorValue
from app.schemas.indicators import (
    IndicatorDetail,
    IndicatorFacets,
    IndicatorListItem,
    IndicatorListResponse,
    IndicatorSearchItem,
    IndicatorSeriesResponse,
    SeriesPoint,
)

COUNTRY_LABELS = {
    "ru": "Россия",
    "us": "США",
    "eu": "Еврозона",
    "cn": "Китай",
    "jp": "Япония",
    "tr": "Турция",
    "world": "Весь мир",
}

CATEGORY_LABELS = {
    "rates": "Ставки и деньги",
    "inflation": "Инфляция и цены",
    "gdp": "ВВП и рост",
    "fx": "Валюты",
    "labor": "Рынок труда",
    "industry": "Промышленность",
    "equities": "Фондовый рынок",
    "commodities": "Сырьё",
}


def _apply_filters(
    query,
    *,
    q: str | None,
    country: list[str] | None,
    category: list[str] | None,
    frequency: list[str] | None,
    source: list[str] | None,
    updated_within_days: int | None,
):
    if q:
        like = f"%{q.strip()}%"
        query = query.where(or_(Indicator.name_ru.ilike(like), Indicator.id.ilike(like)))
    if country:
        query = query.where(Indicator.country.in_(country))
    if category:
        query = query.where(Indicator.category.in_(category))
    if frequency:
        query = query.where(Indicator.frequency.in_(frequency))
    if source:
        query = query.where(Indicator.source.in_(source))
    if updated_within_days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=updated_within_days)
        query = query.where(Indicator.updated_at >= cutoff)
    return query


async def _load_sparklines(session: AsyncSession, indicator_ids: list[str]) -> dict[str, list[float]]:
    if not indicator_ids:
        return {}
    result: dict[str, list[tuple[date, float]]] = {i: [] for i in indicator_ids}
    rows = await session.execute(
        select(IndicatorValue.indicator_id, IndicatorValue.observed_at, IndicatorValue.value)
        .where(IndicatorValue.indicator_id.in_(indicator_ids))
        .order_by(IndicatorValue.indicator_id, IndicatorValue.observed_at)
    )
    for indicator_id, observed_at, value in rows.all():
        result[indicator_id].append((observed_at, value))
    return {k: sparkline_values(v) for k, v in result.items()}


def _to_list_item(row: Indicator, sparkline: list[float]) -> IndicatorListItem:
    return IndicatorListItem(
        id=row.id,
        name_ru=row.name_ru,
        country=row.country,
        category=row.category,
        frequency=row.frequency,
        source=row.source,
        unit=row.unit,
        last_value=format_value(row.last_value, row.unit),
        last_change=format_change(row.last_change, row.unit if row.unit in {"%", "п.п."} else "%"),
        delta_direction=delta_direction(row.last_change),
        updated_at=row.updated_at,
        sparkline=sparkline,
    )


async def list_indicators(
    session: AsyncSession,
    *,
    q: str | None = None,
    country: list[str] | None = None,
    category: list[str] | None = None,
    frequency: list[str] | None = None,
    source: list[str] | None = None,
    updated_within_days: int | None = None,
    sort: str = "name",
    page: int = 1,
    page_size: int = 25,
) -> IndicatorListResponse:
    base = select(Indicator)
    filtered = _apply_filters(
        base,
        q=q,
        country=country,
        category=category,
        frequency=frequency,
        source=source,
        updated_within_days=updated_within_days,
    )

    total = await session.scalar(select(func.count()).select_from(filtered.subquery()))

    if sort == "updated":
        filtered = filtered.order_by(Indicator.updated_at.desc())
    elif sort == "country":
        filtered = filtered.order_by(Indicator.country, Indicator.name_ru)
    else:
        filtered = filtered.order_by(Indicator.name_ru)

    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    rows = await session.scalars(filtered.offset((page - 1) * page_size).limit(page_size))
    items_list = list(rows.all())
    sparklines = await _load_sparklines(session, [r.id for r in items_list])

    return IndicatorListResponse(
        items=[_to_list_item(row, sparklines.get(row.id, [])) for row in items_list],
        total=int(total or 0),
        page=page,
        page_size=page_size,
    )


async def get_facets(session: AsyncSession) -> IndicatorFacets:
    async def counts(column):
        rows = await session.execute(
            select(column, func.count()).group_by(column).order_by(func.count().desc())
        )
        return {str(key): int(count) for key, count in rows.all()}

    return IndicatorFacets(
        countries=await counts(Indicator.country),
        categories=await counts(Indicator.category),
        frequencies=await counts(Indicator.frequency),
        sources=await counts(Indicator.source),
    )


async def get_indicator(session: AsyncSession, indicator_id: str) -> IndicatorDetail | None:
    row = await session.get(Indicator, indicator_id)
    if row is None:
        return None
    sparklines = await _load_sparklines(session, [row.id])
    item = _to_list_item(row, sparklines.get(row.id, []))
    return IndicatorDetail(**item.model_dump(), external_id=row.external_id)


async def get_series(
    session: AsyncSession,
    indicator_id: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> IndicatorSeriesResponse | None:
    indicator = await session.get(Indicator, indicator_id)
    if indicator is None:
        return None

    query = (
        select(IndicatorValue.observed_at, IndicatorValue.value)
        .where(IndicatorValue.indicator_id == indicator_id)
        .order_by(IndicatorValue.observed_at)
    )
    if date_from:
        query = query.where(IndicatorValue.observed_at >= date_from)
    if date_to:
        query = query.where(IndicatorValue.observed_at <= date_to)

    rows = await session.execute(query)
    points = [SeriesPoint(date=observed_at, value=float(value)) for observed_at, value in rows.all()]
    return IndicatorSeriesResponse(indicator_id=indicator_id, unit=indicator.unit, points=points)


async def search_indicators(session: AsyncSession, q: str, limit: int = 10) -> list[IndicatorSearchItem]:
    if not q.strip():
        return []
    like = f"%{q.strip()}%"
    rows = await session.scalars(
        select(Indicator)
        .where(or_(Indicator.name_ru.ilike(like), Indicator.id.ilike(like)))
        .order_by(Indicator.name_ru)
        .limit(min(limit, 20))
    )
    return [
        IndicatorSearchItem(id=row.id, name_ru=row.name_ru, country=row.country, source=row.source)
        for row in rows.all()
    ]


def facet_labels() -> dict[str, dict[str, str]]:
    return {"countries": COUNTRY_LABELS, "categories": CATEGORY_LABELS}
