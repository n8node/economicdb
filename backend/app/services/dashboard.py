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
    KpiItem,
)

KPI_IDS = ["cbr_key_rate", "ru_cpi_yoy", "usd_rub", "us_cpi_yoy", "fed_funds"]

RU_MONTH_ABBR = {
    1: "ЯНВ",
    2: "ФЕВ",
    3: "МАР",
    4: "АПР",
    5: "МАЙ",
    6: "ИЮН",
    7: "ИЮЛ",
    8: "АВГ",
    9: "СЕН",
    10: "ОКТ",
    11: "НОЯ",
    12: "ДЕК",
}

SOURCE_LABELS = {
    "cbr": "Банк России",
    "rosstat": "Росстат",
    "fred": "FRED",
    "oecd": "OECD",
    "ecb": "ECB",
    "eurostat": "Eurostat",
}


def _event_date_label(scheduled_at_msk: datetime) -> str:
    local = scheduled_at_msk
    return f"{local.day} {RU_MONTH_ABBR.get(local.month, '???')}"


def _event_subtext(event: EconomicEvent) -> str | None:
    parts: list[str] = []
    source_label = SOURCE_LABELS.get(event.source, event.source)
    if event.category == "rates":
        if event.forecast is not None:
            parts.append(f"прогноз {format_value(event.forecast, event.unit) or '—'}")
        elif event.previous is not None:
            parts.append(f"пред. {format_value(event.previous, event.unit) or '—'}")
    else:
        if source_label:
            parts.append(source_label)
        if event.forecast is not None:
            parts.append(f"прогноз {format_value(event.forecast, event.unit) or '—'}")
        if event.previous is not None:
            parts.append(f"пред. {format_value(event.previous, event.unit) or '—'}")
    if not parts:
        return None
    return " · ".join(parts[:3])


async def build_dashboard_overview(
    session: AsyncSession,
    ai_summary: AiSummaryBlock | None = None,
    previous_ai_summary: AiSummaryBlock | None = None,
) -> DashboardOverview:
    now = datetime.now(timezone.utc)
    updated_label = now.astimezone(timezone.utc).strftime("%d.%m.%Y, %H:%M МСК")

    indicators = (
        await session.scalars(
            select(Indicator).where(
                Indicator.id.in_(KPI_IDS),
                Indicator.enabled.is_(True),
            )
        )
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
        unit = row.unit if row.unit in {"%", "п.п."} else "%"
        kpis.append(
            KpiItem(
                id=row.id,
                label=row.name_ru,
                value=format_value(row.last_value, row.unit) or "—",
                delta=format_change(row.last_change, unit) or "—",
                delta_direction=delta_direction(row.last_change),
                source=row.source,
                unit=row.unit,
                frequency=row.frequency,
                category=row.category,
                updated_at=row.updated_at.strftime("%d.%m.%Y"),
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
            date_label=_event_date_label(event.scheduled_at_msk),
            time_label=event.scheduled_at_msk.strftime("%H:%M"),
            country=event.country if event.country in {"ru", "eu", "us"} else "ru",
            subtext=_event_subtext(event),
            importance=event.importance if event.importance in {"high", "medium", "low"} else "medium",
        )
        for event in upcoming.all()
    ]

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
        period="—",
        headline="AI-сводка ещё не сгенерирована",
        bullets=[
            "Worker создаст сводку автоматически после ETL и настройки OpenRouter",
            "Или нажмите «Сгенерировать сводку» в /adminus/settings",
        ],
        summary_id=None,
    )

    return DashboardOverview(
        updated_at=updated_label,
        kpis=kpis,
        ai_summary=summary,
        previous_ai_summary=previous_ai_summary,
        calendar_events=calendar_events,
        changes=changes,
    )
