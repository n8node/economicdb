from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.series import delta_direction, format_change, format_value, sparkline_values
from app.models.events import EconomicEvent
from app.models.indicators import Indicator, IndicatorValue
from app.schemas.dashboard import (
    AiSummaryBlock,
    CalendarEventItem,
    ChangeItem,
    DashboardOverview,
    FavoriteItem,
    KpiItem,
)

KPI_IDS = ["cbr_key_rate", "usd_rub", "us_cpi_yoy", "fed_funds", "oil_brent"]
FAVORITE_IDS = ["cbr_key_rate", "usd_rub", "ru_cpi_yoy", "us_cpi_yoy", "fed_funds"]


async def build_dashboard_overview(session: AsyncSession, ai_summary: AiSummaryBlock | None = None) -> DashboardOverview:
    now = datetime.now(timezone.utc)
    updated_label = now.astimezone(timezone.utc).strftime("%d.%m.%Y, %H:%M МСК")

    indicators = (
        await session.scalars(select(Indicator).where(Indicator.id.in_(KPI_IDS + FAVORITE_IDS)))
    ).all()
    indicator_map = {i.id: i for i in indicators}

    sparkline_map: dict[str, list[float]] = {}
    if KPI_IDS:
        rows = await session.execute(
            select(IndicatorValue.indicator_id, IndicatorValue.observed_at, IndicatorValue.value)
            .where(IndicatorValue.indicator_id.in_(KPI_IDS))
            .order_by(IndicatorValue.indicator_id, IndicatorValue.observed_at)
        )
        raw: dict[str, list] = {i: [] for i in KPI_IDS}
        for indicator_id, observed_at, value in rows.all():
            raw[indicator_id].append((observed_at, value))
        sparkline_map = {k: sparkline_values(v) for k, v in raw.items()}

    kpis: list[KpiItem] = []
    for indicator_id in KPI_IDS:
        row = indicator_map.get(indicator_id)
        if not row:
            continue
        kpis.append(
            KpiItem(
                label=row.name_ru,
                value=format_value(row.last_value, row.unit) or "—",
                delta=format_change(row.last_change, row.unit if row.unit in {"%", "п.п."} else "%") or "—",
                delta_direction=delta_direction(row.last_change),
                sparkline=sparkline_map.get(indicator_id, []),
            )
        )

    upcoming = await session.scalars(
        select(EconomicEvent)
        .where(EconomicEvent.scheduled_at_msk >= now)
        .order_by(EconomicEvent.scheduled_at_msk)
        .limit(3)
    )
    calendar_events = [
        CalendarEventItem(
            title=event.title_ru,
            time=event.scheduled_at_msk.strftime("%d %B, %H:%M МСК"),
            country=event.country if event.country in {"ru", "eu", "us"} else "ru",
        )
        for event in upcoming.all()
    ]

    favorites: list[FavoriteItem] = []
    for indicator_id in FAVORITE_IDS:
        row = indicator_map.get(indicator_id)
        if not row:
            continue
        favorites.append(
            FavoriteItem(
                label=row.name_ru,
                value=format_value(row.last_value, row.unit) or "—",
                delta=format_change(row.last_change, row.unit if row.unit in {"%", "п.п."} else "%") or "—",
                delta_direction=delta_direction(row.last_change),
                source=row.source,
            )
        )

    surprises = await session.scalars(
        select(EconomicEvent)
        .where(EconomicEvent.surprise.is_not(None))
        .order_by(EconomicEvent.scheduled_at_msk.desc())
        .limit(3)
    )
    changes: list[ChangeItem] = []
    for event in surprises.all():
        direction = "up" if event.surprise and float(event.surprise) > 0 else "down" if event.surprise and float(event.surprise) < 0 else "flat"
        changes.append(
            ChangeItem(
                direction=direction,
                text=f"{event.title_ru}: факт {format_value(event.actual, event.unit) or '—'} vs прогноз {format_value(event.forecast, event.unit) or '—'}",
                meta=f"{event.source.upper()} · {event.scheduled_at_msk.strftime('%d.%m.%Y')}",
            )
        )

    summary = ai_summary or AiSummaryBlock(
        period="Реальные данные",
        headline="AI-сводка появится после подключения OpenRouter и генерации worker-ом",
        bullets=[
            "Показатели на дашборде загружаются только из подключённых провайдеров",
            "Фейковые события и demo-сводки отключены",
            "Числа в AI-блоках будут использовать только Facts JSON из реальных рядов",
        ],
    )

    return DashboardOverview(
        updated_at=updated_label,
        kpis=kpis,
        ai_summary=summary,
        calendar_events=calendar_events,
        favorites=favorites,
        changes=changes,
    )
