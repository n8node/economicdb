from __future__ import annotations

from datetime import date

from app.integrations.imf.client import ImfError, fetch_gdp_yoy_series
from app.models.indicators import Indicator


def _split_code_country(external_id: str) -> tuple[str, str]:
    if "/" not in external_id:
        raise ValueError("bad_external_id")
    code, country = external_id.rsplit("/", 1)
    return code.strip(), country.strip()


async def fetch_indicator_series(
    indicator: Indicator,
    *,
    from_date: date,
    to_date: date,
) -> tuple[list[tuple[date, object]], str]:
    external_id = (indicator.external_id or "").strip()
    if not external_id:
        raise ImfError(f"Нет external_id для {indicator.id}", code="imf_missing_external_id")
    try:
        indicator_code, country_code = _split_code_country(external_id)
    except ValueError as exc:
        raise ImfError(f"Неверный external_id: {external_id}", code="imf_bad_external_id") from exc
    series = await fetch_gdp_yoy_series(indicator_code, country_code, from_date=from_date, to_date=to_date)
    if not series:
        raise ImfError(f"Пустой ряд IMF {external_id}", code="imf_empty_series")
    return series, external_id
