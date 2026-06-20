from __future__ import annotations

from datetime import date

from app.integrations.oecd.client import OecdError, fetch_sdmx_series
from app.models.indicators import Indicator


async def fetch_indicator_series(
    indicator: Indicator,
    *,
    from_date: date,
    to_date: date,
) -> tuple[list[tuple[date, object]], str]:
    external_id = (indicator.external_id or "").strip()
    if not external_id:
        raise OecdError(f"Нет external_id для {indicator.id}", code="oecd_missing_external_id")
    series = await fetch_sdmx_series(external_id, from_date=from_date, to_date=to_date)
    if not series:
        raise OecdError(f"Пустой ряд OECD {external_id}", code="oecd_empty_series")
    return series, external_id
