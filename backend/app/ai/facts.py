from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.series import format_change, format_value
from app.core.timezones import MSK
from app.models.events import EconomicEvent
from app.models.indicators import Indicator

DIGEST_INDICATOR_IDS: dict[str, list[str]] = {
    "ru": ["cbr_key_rate", "usd_rub", "ru_cpi_yoy", "ru_industrial_yoy"],
    "us": ["fed_funds", "us_cpi_yoy", "us_gdp_yoy"],
    "eu": ["ecb_deposit_rate", "eu_hicp_yoy"],
    "markets": ["oil_brent", "usd_rub", "eur_rub"],
}

SOURCE_LABELS = {
    "cbr": "Банк России",
    "rosstat": "Росстат",
    "fred": "FRED",
    "oecd": "OECD",
    "ecb": "ECB",
    "eurostat": "Eurostat",
    "imf": "IMF",
    "world_bank": "World Bank",
    "moex": "MOEX",
}


@dataclass
class CitationFact:
    key: str
    indicator_id: str
    label: str
    value: str
    change: str | None
    source: str
    country: str


@dataclass
class KPIFact:
    indicator_id: str
    label: str
    country: str
    category: str
    value: str
    change: str | None
    source: str
    updated_at: str | None
    citation_key: str


@dataclass
class SurpriseFact:
    event_id: str
    title: str
    country: str
    actual: str | None
    forecast: str | None
    surprise: str | None
    source: str
    scheduled_at: str


@dataclass
class EventFact:
    event_id: str
    title: str
    country: str
    importance: str
    scheduled_at: str
    source: str


@dataclass
class FactsJSON:
    period_start: date
    period_end: date
    period_label: str
    kpis: list[KPIFact] = field(default_factory=list)
    calendar_surprises: list[SurpriseFact] = field(default_factory=list)
    next_week_events: list[EventFact] = field(default_factory=list)
    citation_keys: dict[str, CitationFact] = field(default_factory=dict)

    def all_numeric_values(self) -> set[float]:
        values: set[float] = set()
        for fact in self.kpis:
            values |= _numbers_from_text(fact.value)
            if fact.change:
                values |= _numbers_from_text(fact.change)
        for surprise in self.calendar_surprises:
            for part in (surprise.actual, surprise.forecast, surprise.surprise):
                if part:
                    values |= _numbers_from_text(part)
        for citation in self.citation_keys.values():
            values |= _numbers_from_text(citation.value)
            if citation.change:
                values |= _numbers_from_text(citation.change)
        return values

    def to_prompt_dict(self) -> dict:
        return {
            "period_label": self.period_label,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "kpis": [
                {
                    "citation_key": item.citation_key,
                    "indicator_id": item.indicator_id,
                    "label": item.label,
                    "country": item.country,
                    "value": item.value,
                    "change": item.change,
                    "source": item.source,
                }
                for item in self.kpis
            ],
            "calendar_surprises": [
                {
                    "title": item.title,
                    "country": item.country,
                    "actual": item.actual,
                    "forecast": item.forecast,
                    "surprise": item.surprise,
                    "source": item.source,
                    "scheduled_at": item.scheduled_at,
                }
                for item in self.calendar_surprises
            ],
            "next_week_events": [
                {
                    "title": item.title,
                    "country": item.country,
                    "importance": item.importance,
                    "scheduled_at": item.scheduled_at,
                    "source": item.source,
                }
                for item in self.next_week_events
            ],
            "citation_keys": {
                key: {
                    "label": item.label,
                    "value": item.value,
                    "change": item.change,
                    "source": item.source,
                    "indicator_id": item.indicator_id,
                }
                for key, item in self.citation_keys.items()
            },
        }


def resolve_digest_period(now: datetime | None = None) -> tuple[date, date, str]:
    current = (now or datetime.now(MSK)).astimezone(MSK)
    period_end = current.date()
    period_start = period_end - timedelta(days=6)
    return period_start, period_end, _format_period_label(period_start, period_end)


def build_summary_id(period_end: date) -> str:
    iso = period_end.isocalendar()
    return f"ws_{iso.year}_w{iso.week:02d}"


def _format_period_label(start: date, end: date) -> str:
    if start.month == end.month:
        return f"{start.day}–{end.day} {_month_name(end.month)} {end.year}"
    return f"{start.day} {_month_name(start.month)} – {end.day} {_month_name(end.month)} {end.year}"


def _month_name(month: int) -> str:
    names = {
        1: "января",
        2: "февраля",
        3: "марта",
        4: "апреля",
        5: "мая",
        6: "июня",
        7: "июля",
        8: "августа",
        9: "сентября",
        10: "октября",
        11: "ноября",
        12: "декабря",
    }
    return names.get(month, "")


def _numbers_from_text(text: str) -> set[float]:
    import re

    values: set[float] = set()
    for match in re.finditer(r"-?\d+[,.]?\d*", text):
        raw = match.group(0).replace(",", ".")
        try:
            values.add(round(float(raw), 4))
        except ValueError:
            continue
    return values


async def build_weekly_facts(
    session: AsyncSession,
    *,
    period_start: date | None = None,
    period_end: date | None = None,
) -> FactsJSON:
    if period_start is None or period_end is None:
        period_start, period_end, period_label = resolve_digest_period()
    else:
        period_label = _format_period_label(period_start, period_end)

    facts = FactsJSON(
        period_start=period_start,
        period_end=period_end,
        period_label=period_label,
    )

    indicator_ids = sorted({indicator_id for ids in DIGEST_INDICATOR_IDS.values() for indicator_id in ids})
    rows = await session.scalars(
        select(Indicator).where(Indicator.id.in_(indicator_ids), Indicator.enabled.is_(True))
    )
    indicators = {row.id: row for row in rows.all()}

    for indicator_id in indicator_ids:
        row = indicators.get(indicator_id)
        if row is None or row.last_value is None:
            continue
        value = format_value(row.last_value, row.unit) or "—"
        change = format_change(row.last_change, row.unit if row.unit in {"%", "п.п."} else "%")
        citation_key = indicator_id
        kpi = KPIFact(
            indicator_id=indicator_id,
            label=row.name_ru,
            country=row.country,
            category=row.category,
            value=value,
            change=change,
            source=SOURCE_LABELS.get(row.source, row.source),
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
            citation_key=citation_key,
        )
        facts.kpis.append(kpi)
        facts.citation_keys[citation_key] = CitationFact(
            key=citation_key,
            indicator_id=indicator_id,
            label=row.name_ru,
            value=value,
            change=change,
            source=SOURCE_LABELS.get(row.source, row.source),
            country=row.country,
        )

    period_start_dt = datetime.combine(period_start, datetime.min.time(), tzinfo=MSK)
    period_end_dt = datetime.combine(period_end, datetime.max.time(), tzinfo=MSK)

    surprise_rows = await session.scalars(
        select(EconomicEvent)
        .where(
            and_(
                EconomicEvent.scheduled_at_msk >= period_start_dt,
                EconomicEvent.scheduled_at_msk <= period_end_dt,
                EconomicEvent.surprise.is_not(None),
            )
        )
        .order_by(EconomicEvent.scheduled_at_msk.desc())
        .limit(8)
    )
    for event in surprise_rows.all():
        facts.calendar_surprises.append(
            SurpriseFact(
                event_id=event.id,
                title=event.title_ru,
                country=event.country,
                actual=format_value(event.actual, event.unit),
                forecast=format_value(event.forecast, event.unit),
                surprise=format_value(event.surprise, event.unit),
                source=SOURCE_LABELS.get(event.source, event.source),
                scheduled_at=event.scheduled_at_msk.astimezone(MSK).strftime("%d.%m.%Y"),
            )
        )

    next_week_end = period_end_dt + timedelta(days=7)
    upcoming_rows = await session.scalars(
        select(EconomicEvent)
        .where(
            and_(
                EconomicEvent.scheduled_at_msk > period_end_dt,
                EconomicEvent.scheduled_at_msk <= next_week_end,
                EconomicEvent.importance.in_(["high", "med"]),
            )
        )
        .order_by(EconomicEvent.scheduled_at_msk)
        .limit(12)
    )
    for event in upcoming_rows.all():
        facts.next_week_events.append(
            EventFact(
                event_id=event.id,
                title=event.title_ru,
                country=event.country,
                importance=event.importance,
                scheduled_at=event.scheduled_at_msk.astimezone(MSK).strftime("%d.%m.%Y, %H:%M"),
                source=SOURCE_LABELS.get(event.source, event.source),
            )
        )

    return facts
