from __future__ import annotations

from datetime import date

from app.integrations.ecb_eurostat.client import (
    EcbEurostatError,
    fetch_ecb_series_by_key,
    fetch_eurostat_series_by_key,
)
from app.models.indicators import Indicator


async def fetch_indicator_series(
    indicator: Indicator,
    *,
    from_date: date,
    to_date: date,
) -> tuple[list[tuple[date, object]], str]:
    external_id = (indicator.external_id or "").strip()
    if not external_id:
        raise EcbEurostatError(f"Нет external_id для {indicator.id}", code="ecb_eurostat_missing_external_id")

    if indicator.source == "ecb":
        series = await fetch_ecb_series_by_key(external_id, from_date=from_date, to_date=to_date)
    elif indicator.source == "eurostat":
        series = await fetch_eurostat_series_by_key(external_id, from_date=from_date, to_date=to_date)
    else:
        raise EcbEurostatError(f"Неизвестный источник {indicator.source}", code="ecb_eurostat_bad_source")

    if not series:
        raise EcbEurostatError(f"Пустой ряд {external_id}", code="ecb_eurostat_empty_series")
    return series, external_id
