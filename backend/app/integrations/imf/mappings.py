from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImfSeriesMapping:
    indicator_id: str
    indicator_code: str
    country_code: str
    series_type: str


IMF_MAPPINGS: list[ImfSeriesMapping] = [
    ImfSeriesMapping(
        indicator_id="cn_gdp_yoy",
        indicator_code="NGDP_RPCH",
        country_code="CHN",
        series_type="gdp_yoy",
    ),
]
