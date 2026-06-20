from __future__ import annotations

from datetime import date

from app.integrations.fred.client import FredError, fetch_observations
from app.integrations.fred.transforms import apply_transform
from app.models.indicators import Indicator

FRED_TRANSFORMS: dict[str, str] = {
    "fed_funds": "direct",
    "us_cpi_yoy": "yoy_percent",
    "us_core_cpi_yoy": "yoy_percent",
    "us_pce_yoy": "yoy_percent",
    "us_nfp": "mom_diff",
    "us_gdp_yoy": "direct",
    "us_indpro_yoy": "yoy_percent",
    "us_10y_yield": "direct",
    "us_unemployment": "direct",
    "sp500": "direct",
    "oil_brent": "direct",
    "oil_wti": "direct",
}


def fred_transform_for(indicator: Indicator) -> str:
    if indicator.id in FRED_TRANSFORMS:
        return FRED_TRANSFORMS[indicator.id]
    if indicator.id.endswith("_yoy") or "yoy" in indicator.id:
        return "yoy_percent"
    return "direct"


async def fetch_indicator_series(
    indicator: Indicator,
    api_key: str,
    *,
    from_date: date,
    to_date: date,
) -> tuple[list[tuple[date, object]], str]:
    series_id = (indicator.external_id or "").strip()
    if not series_id:
        raise FredError(f"Нет external_id для {indicator.id}", code="fred_missing_external_id")

    raw = await fetch_observations(
        api_key,
        series_id,
        observation_start=from_date.isoformat(),
    )
    transform = fred_transform_for(indicator)
    series = apply_transform(transform, raw)
    series = [(observed, value) for observed, value in series if observed <= to_date]
    if not series and indicator.id == "gold_spot" and series_id == "GOLDPMGBD228NLBM":
        fallback_id = "GOLDAMGBD228NLBM"
        raw = await fetch_observations(
            api_key,
            fallback_id,
            observation_start=from_date.isoformat(),
        )
        series = apply_transform(transform, raw)
        series = [(observed, value) for observed, value in series if observed <= to_date]
        if series:
            return series, fallback_id
    if not series:
        raise FredError(f"Пустой ряд FRED {series_id}", code="fred_empty_series")
    return series, series_id
