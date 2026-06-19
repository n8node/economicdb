from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FredSeriesMapping:
    indicator_id: str
    series_id: str
    transform: str = "direct"


FRED_MAPPINGS: list[FredSeriesMapping] = [
    FredSeriesMapping("fed_funds", "FEDFUNDS", "direct"),
    FredSeriesMapping("us_cpi_yoy", "CPIAUCSL", "yoy_percent"),
    FredSeriesMapping("us_nfp", "PAYEMS", "mom_diff"),
    FredSeriesMapping("us_gdp_yoy", "A191RL1Q225SBEA", "direct"),
    FredSeriesMapping("oil_brent", "DCOILBRENTEU", "direct"),
]
