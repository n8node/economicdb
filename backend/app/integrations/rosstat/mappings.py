from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RosstatSeriesMapping:
    indicator_id: str
    series_type: str


ROSSTAT_MAPPINGS: list[RosstatSeriesMapping] = [
    RosstatSeriesMapping("ru_cpi_yoy", "cpi_yoy"),
]
