from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.integrations.rosstat.client import RosstatError, fetch_cpi_yoy_from_cbr
from app.integrations.rosstat.fedstat import fetch_fedstat_series
from app.models.indicators import Indicator

FEDSTAT_PREFIX = "fedstat:"


@dataclass(frozen=True)
class FedstatConfig:
    series_key: dict[str, str]
    transform: str = "index_yoy"
    fallback_cbr_cpi: bool = False


FEDSTAT_CONFIG: dict[str, FedstatConfig] = {
    "31074": FedstatConfig(
        series_key={"s_OKATO": "030", "s_grtov": "2", "s_POK": "9"},
        transform="index_yoy",
        fallback_cbr_cpi=True,
    ),
    "57806": FedstatConfig(
        series_key={"s_OKATO": "643004.АГ", "s_OKVED2": "1323500.029.31", "s_POK": "3"},
        transform="index_yoy",
    ),
    "42934": FedstatConfig(
        series_key={"s_OKATO": "643", "s_POK": "3"},
        transform="index_yoy",
    ),
    "57614": FedstatConfig(
        series_key={"s_OKATO": "643", "s_POK": "1"},
        transform="direct",
    ),
    "57746": FedstatConfig(
        series_key={"s_OKATO": "643", "s_POK": "30"},
        transform="index_yoy",
    ),
}


def parse_fedstat_id(external_id: str) -> str | None:
    if external_id.startswith(FEDSTAT_PREFIX):
        return external_id.removeprefix(FEDSTAT_PREFIX).split("/", 1)[0]
    return None


async def fetch_indicator_series(
    indicator: Indicator,
    *,
    from_date: date,
    to_date: date,
) -> tuple[list[tuple[date, object]], str]:
    external_id = (indicator.external_id or "").strip()
    fedstat_id = parse_fedstat_id(external_id)
    if not fedstat_id:
        raise RosstatError(f"Нет fedstat external_id для {indicator.id}", code="rosstat_missing_external_id")

    config = FEDSTAT_CONFIG.get(fedstat_id)
    if config is None:
        raise RosstatError(
            f"Нет конфигурации fedstat для {fedstat_id} ({indicator.id})",
            code="rosstat_unconfigured",
        )

    if fedstat_id == "31074" and config.fallback_cbr_cpi:
        try:
            series = await fetch_fedstat_series(
                fedstat_id,
                series_key=config.series_key,
                transform=config.transform,
                from_date=from_date,
                to_date=to_date,
            )
            return series, external_id
        except RosstatError:
            series = await fetch_cpi_yoy_from_cbr(from_date=from_date, to_date=to_date)
            return series, external_id

    series = await fetch_fedstat_series(
        fedstat_id,
        series_key=config.series_key,
        transform=config.transform,
        from_date=from_date,
        to_date=to_date,
    )
    if not series:
        raise RosstatError(f"Пустой ряд fedstat {fedstat_id}", code="rosstat_empty_series")
    return series, external_id
