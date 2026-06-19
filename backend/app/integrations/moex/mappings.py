from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MoexSeriesMapping:
    indicator_id: str
    engine: str
    market: str
    security: str
    value_column: str
    series_type: str


MOEX_MAPPINGS: list[MoexSeriesMapping] = [
    MoexSeriesMapping(
        indicator_id="imoex",
        engine="stock",
        market="index",
        security="IMOEX",
        value_column="CLOSE",
        series_type="index_close",
    ),
]
