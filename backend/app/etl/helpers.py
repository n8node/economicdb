from __future__ import annotations

from datetime import date, datetime, timezone

from app.etl.options import SyncOptions
from app.models.indicators import Indicator

PROVIDER_SOURCES: dict[str, list[str]] = {
    "cbr": ["cbr"],
    "rosstat": ["rosstat"],
    "fred": ["fred"],
    "oecd": ["oecd"],
    "imf": ["imf"],
    "ecb_eurostat": ["ecb", "eurostat"],
    "world_bank": ["world_bank"],
    "moex": ["moex"],
}


def resolve_date_range(options: SyncOptions | None) -> tuple[date, date]:
    today = datetime.now(timezone.utc).date()
    to_date = options.date_to if options and options.date_to else today
    if options and options.date_from:
        from_date = options.date_from
    else:
        from_date = date(to_date.year - 5, 1, 1)
    if from_date > to_date:
        from_date, to_date = to_date, from_date
    return from_date, to_date


def indicator_matches_options(indicator: Indicator | None, options: SyncOptions | None) -> bool:
    if indicator is None:
        return False
    if options is None:
        return True
    if not options.allows_indicator(indicator.id):
        return False
    return options.allows_country(indicator.country)


def sources_for_provider(provider_id: str) -> list[str]:
    return PROVIDER_SOURCES.get(provider_id, [])
