from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EcbEurostatSeriesMapping:
    indicator_id: str
    series_type: str
    external_id: str


ECB_EUROSTAT_MAPPINGS: list[EcbEurostatSeriesMapping] = [
    EcbEurostatSeriesMapping(
        indicator_id="ecb_deposit_rate",
        series_type="ecb_deposit_rate",
        external_id="FM/D.U2.EUR.4F.KR.DFR.LEV",
    ),
    EcbEurostatSeriesMapping(
        indicator_id="eu_hicp_yoy_eurostat",
        series_type="eurostat_hicp_yoy",
        external_id="PRC_HICP_MANR/M.RCH_A.CP00.EA20",
    ),
]
