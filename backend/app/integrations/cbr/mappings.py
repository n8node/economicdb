from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CbrSeriesMapping:
    indicator_id: str
    series_type: str
    valuta_code: str | None = None


CBR_MAPPINGS: list[CbrSeriesMapping] = [
    CbrSeriesMapping("cbr_key_rate", "key_rate"),
    CbrSeriesMapping("usd_rub", "usd_rub", valuta_code="R01235"),
]
