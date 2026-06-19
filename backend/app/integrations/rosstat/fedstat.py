from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal
from typing import Iterable

import httpx
import structlog

from app.integrations.rosstat.client import (
    DEFAULT_FROM_DATE,
    HTTP_HEADERS,
    HTTP_RETRIES,
    HTTP_TIMEOUT,
    RosstatError,
    _parse_decimal,
)

logger = structlog.get_logger()

FEDSTAT_DATA_URL = "https://www.fedstat.ru/indicator/data.do?format=sdmx"
NS = {"g": "http://www.SDMX.org/resources/SDMXML/schemas/v1_0/generic"}

MONTHS_RU = {
    "январь": 1,
    "февраль": 2,
    "март": 3,
    "апрель": 4,
    "май": 5,
    "июнь": 6,
    "июль": 7,
    "август": 8,
    "сентябрь": 9,
    "октябрь": 10,
    "ноябрь": 11,
    "декабрь": 12,
}


def _parse_month_period(raw: str) -> int | None:
    cleaned = raw.strip().lower()
    if cleaned in MONTHS_RU:
        return MONTHS_RU[cleaned]
    match = re.match(r"^(\d{1,2})$", cleaned)
    if match:
        month = int(match.group(1))
        if 1 <= month <= 12:
            return month
    return None


def _transform_value(value: Decimal, transform: str) -> Decimal:
    if transform == "index_yoy":
        return (value - Decimal("100")).quantize(Decimal("0.01"))
    return value


def _series_matches(series_key_el: ET.Element, expected: dict[str, str]) -> bool:
    values: dict[str, str] = {}
    for child in series_key_el:
        tag = child.tag.split("}")[-1]
        if tag != "Value":
            continue
        concept = child.attrib.get("concept")
        if concept:
            values[concept] = child.attrib.get("value", "")
    return all(values.get(key) == val for key, val in expected.items())


def parse_fedstat_sdmx_series(
    xml_text: str,
    *,
    series_key: dict[str, str],
    transform: str = "index_yoy",
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date,
) -> list[tuple[date, Decimal]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise RosstatError(f"Не удалось разобрать SDMX fedstat ({exc})", code="rosstat_parse_error") from exc

    points: list[tuple[date, Decimal]] = []
    for series_el in root.findall(".//g:Series", NS):
        key_el = series_el.find("g:SeriesKey", NS)
        if key_el is None or not _series_matches(key_el, series_key):
            continue

        period_text = ""
        attrs_el = series_el.find("g:Attributes", NS)
        if attrs_el is not None:
            for attr in attrs_el.findall("g:Value", NS):
                if attr.attrib.get("concept") == "PERIOD":
                    period_text = attr.attrib.get("value", "")
                    break

        month = _parse_month_period(period_text)
        if month is None:
            continue

        for obs_el in series_el.findall("g:Obs", NS):
            time_el = obs_el.find("g:Time", NS)
            value_el = obs_el.find("g:ObsValue", NS)
            if time_el is None or value_el is None:
                continue
            try:
                year = int(time_el.text or "")
            except ValueError:
                continue
            observed = date(year, month, 1)
            if observed < from_date.replace(day=1) or observed > to_date:
                continue
            raw_value = _parse_decimal(value_el.attrib.get("value", ""))
            if raw_value is None:
                continue
            points.append((observed, _transform_value(raw_value, transform)))

    series = sorted(points, key=lambda item: item[0])
    if not series:
        raise RosstatError("Не удалось извлечь ряд из fedstat SDMX", code="rosstat_parse_error")
    return series


async def fetch_fedstat_sdmx(indicator_id: str) -> str:
    errors: list[str] = []
    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            async with httpx.AsyncClient(
                timeout=HTTP_TIMEOUT,
                follow_redirects=True,
                headers=HTTP_HEADERS,
                trust_env=False,
            ) as client:
                response = await client.post(
                    FEDSTAT_DATA_URL,
                    data={"id": indicator_id},
                )
            if response.status_code >= 400:
                errors.append(f"HTTP {response.status_code}")
                break
            text = response.text
            if "<GenericData" not in text:
                errors.append("ответ не SDMX")
                break
            logger.info(
                "fedstat_http_post_ok",
                indicator_id=indicator_id,
                attempt=attempt,
                bytes=len(response.content),
            )
            return text
        except httpx.TimeoutException:
            errors.append(f"timeout (attempt {attempt})")
        except httpx.HTTPError as exc:
            errors.append(str(exc))
            break
    if any("timeout" in item for item in errors):
        raise RosstatError("fedstat.ru не ответил вовремя", code="rosstat_timeout")
    raise RosstatError(f"Не удалось загрузить fedstat ({'; '.join(errors)})", code="rosstat_network_error")


async def fetch_fedstat_series(
    indicator_id: str,
    *,
    series_key: dict[str, str],
    transform: str = "index_yoy",
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date,
) -> list[tuple[date, Decimal]]:
    xml_text = await fetch_fedstat_sdmx(indicator_id)
    return parse_fedstat_sdmx_series(
        xml_text,
        series_key=series_key,
        transform=transform,
        from_date=from_date,
        to_date=to_date,
    )


def merge_series(chunks: Iterable[list[tuple[date, Decimal]]]) -> list[tuple[date, Decimal]]:
    merged: dict[date, Decimal] = {}
    for chunk in chunks:
        for observed, value in chunk:
            merged[observed] = value
    return sorted(merged.items(), key=lambda item: item[0])
