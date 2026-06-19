from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OecdSeriesMapping:
    indicator_id: str
    series_key: str
    series_type: str


# SDMX key dimensions: REF_AREA.FREQ.METHODOLOGY.MEASURE.UNIT_MEASURE.EXPENDITURE.ADJUSTMENT.TRANSFORMATION
OECD_MAPPINGS: list[OecdSeriesMapping] = [
    OecdSeriesMapping(
        indicator_id="eu_hicp_yoy",
        series_key="EA20.M.HICP.CPI.PA._T.N.GY",
        series_type="hicp_yoy",
    ),
]
