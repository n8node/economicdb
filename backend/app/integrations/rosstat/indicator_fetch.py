from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.integrations.rosstat.client import RosstatError, fetch_cpi_yoy_from_cbr
from app.integrations.rosstat.fedstat import fetch_fedstat_series, fetch_fedstat_with_filters
from app.models.indicators import Indicator

FEDSTAT_PREFIX = "fedstat:"


@dataclass(frozen=True)
class FedstatConfig:
    series_key: dict[str, str] | None = None
    filters: dict[str, str | list[str]] | None = None
    transform: str = "index_yoy"
    fallback_cbr_cpi: bool = False

    def __post_init__(self) -> None:
        if not self.series_key and not self.filters:
            raise ValueError("FedstatConfig requires series_key or filters")
        if self.series_key and self.filters:
            raise ValueError("FedstatConfig accepts either series_key or filters, not both")


FEDSTAT_CONFIG: dict[str, FedstatConfig] = {
    "31074": FedstatConfig(
        filters={
            "Классификатор объектов административно-территориального деления (ОКАТО)": "Российская Федерация",
            "Виды показателя": "К соответствующему периоду предыдущего года",
            "Виды товаров и услуг": "Все товары и услуги",
        },
        transform="index_yoy",
        fallback_cbr_cpi=True,
    ),
    "31074/food": FedstatConfig(
        filters={
            "Классификатор объектов административно-территориального деления (ОКАТО)": "Российская Федерация",
            "Виды показателя": "К соответствующему периоду предыдущего года",
            "Виды товаров и услуг": "Продовольственные товары",
        },
        transform="index_yoy",
    ),
    "31074/services": FedstatConfig(
        filters={
            "Классификатор объектов административно-территориального деления (ОКАТО)": "Российская Федерация",
            "Виды показателя": "К соответствующему периоду предыдущего года",
            "Виды товаров и услуг": "Услуги (без услуг необязательного пользования)",
        },
        transform="index_yoy",
    ),
    "57806": FedstatConfig(
        series_key={"s_OKATO": "643004.АГ", "s_OKVED2": "1323500.029.31", "s_POK": "3"},
        transform="index_yoy",
    ),
    "31066": FedstatConfig(
        series_key={"s_OKATO": "643004.АГ", "s_POK": "9", "s_formtorg": "1"},
        transform="index_yoy",
    ),
    "43062": FedstatConfig(
        series_key={"s_OKATO": "643", "s_vozr": "207"},
        transform="direct",
    ),
    "57746": FedstatConfig(
        series_key={"s_OKATO": "643", "s_POK": "30"},
        transform="index_yoy",
    ),
    "31077": FedstatConfig(
        series_key={"s_OKATO": "643", "s_POK": "21"},
        transform="volume_index_yoy",
    ),
    "57609": FedstatConfig(
        series_key={
            "s_OKATO": "643004.АГ",
            "s_OKVED2": "1323500.029.31",
            "s_POK": "9",
            "s_kanalreal": "1",
        },
        transform="index_yoy",
    ),
    "31081": FedstatConfig(
        filters={
            "Классификатор объектов административно-территориального деления (ОКАТО)": "Российская Федерация",
            "Виды показателя": "К соответствующему периоду предыдущего года",
        },
        transform="index_yoy",
    ),
}


def parse_fedstat_config_key(external_id: str) -> str | None:
    if external_id.startswith(FEDSTAT_PREFIX):
        return external_id.removeprefix(FEDSTAT_PREFIX)
    return None


def parse_fedstat_id(external_id: str) -> str | None:
    config_key = parse_fedstat_config_key(external_id)
    if config_key is None:
        return None
    return config_key.split("/", 1)[0]


def fedstat_indicator_id(config_key: str) -> str:
    return config_key.split("/", 1)[0]


async def fetch_indicator_series(
    indicator: Indicator,
    *,
    from_date: date,
    to_date: date,
) -> tuple[list[tuple[date, object]], str]:
    external_id = (indicator.external_id or "").strip()
    config_key = parse_fedstat_config_key(external_id)
    if not config_key:
        raise RosstatError(f"Нет fedstat external_id для {indicator.id}", code="rosstat_missing_external_id")

    config = FEDSTAT_CONFIG.get(config_key)
    if config is None:
        raise RosstatError(
            f"Нет конфигурации fedstat для {config_key} ({indicator.id})",
            code="rosstat_unconfigured",
        )

    indicator_id = fedstat_indicator_id(config_key)

    async def _fetch() -> list[tuple[date, object]]:
        if config.filters:
            return await fetch_fedstat_with_filters(
                indicator_id,
                filters=config.filters,
                transform=config.transform,
                from_date=from_date,
                to_date=to_date,
            )
        return await fetch_fedstat_series(
            indicator_id,
            series_key=config.series_key or {},
            transform=config.transform,
            from_date=from_date,
            to_date=to_date,
        )

    if config_key == "31074" and config.fallback_cbr_cpi:
        try:
            series = await _fetch()
            return series, external_id
        except RosstatError:
            series = await fetch_cpi_yoy_from_cbr(from_date=from_date, to_date=to_date)
            return series, external_id

    series = await _fetch()
    if not series:
        raise RosstatError(f"Пустой ряд fedstat {config_key}", code="rosstat_empty_series")
    return series, external_id
