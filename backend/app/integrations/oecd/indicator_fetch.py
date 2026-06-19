from __future__ import annotations

from datetime import date

from app.integrations.oecd.client import OecdError, fetch_hicp_yoy_series
from app.models.indicators import Indicator


async def fetch_indicator_series(
    indicator: Indicator,
    *,
    from_date: date,
    to_date: date,
) -> tuple[list[tuple[date, object]], str]:
    series_key = (indicator.external_id or "").strip()
    if not series_key:
        raise OecdError(f"Нет external_id для {indicator.id}", code="oecd_missing_external_id")
    series = await fetch_hicp_yoy_series(series_key, from_date=from_date, to_date=to_date)
    if not series:
        raise OecdError(f"Пустой ряд OECD {series_key}", code="oecd_empty_series")
    return series, series_key
