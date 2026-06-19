from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorldBankSeriesMapping:
    indicator_id: str
    country_code: str
    indicator_code: str
    series_type: str


WORLD_BANK_MAPPINGS: list[WorldBankSeriesMapping] = [
    WorldBankSeriesMapping(
        indicator_id="ru_gdp_yoy_wb",
        country_code="RU",
        indicator_code="NY.GDP.MKTP.KD.ZG",
        series_type="gdp_growth",
    ),
]
