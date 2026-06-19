from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RosstatSeriesMapping:
    indicator_id: str
    series_type: str
    fedstat_indicator_id: str | None = None
    fedstat_series_key: dict[str, str] | None = None
    fedstat_transform: str = "index_yoy"


ROSSTAT_MAPPINGS: list[RosstatSeriesMapping] = [
    RosstatSeriesMapping(
        indicator_id="ru_cpi_yoy",
        series_type="cpi_yoy",
        fedstat_indicator_id="31074",
        fedstat_series_key={"s_OKATO": "030", "s_grtov": "2", "s_POK": "9"},
    ),
    RosstatSeriesMapping(
        indicator_id="ru_industrial_yoy",
        series_type="industrial_yoy",
        fedstat_indicator_id="57806",
        fedstat_series_key={
            "s_OKATO": "643004.АГ",
            "s_OKVED2": "1323500.029.31",
            "s_POK": "3",
        },
    ),
]
