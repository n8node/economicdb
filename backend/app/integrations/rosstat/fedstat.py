from __future__ import annotations

import re
import unicodedata
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


def _normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", value.strip())


def _local_tag(element: ET.Element) -> str:
    tag = element.tag
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _series_matches(series_key_el: ET.Element, expected: dict[str, str]) -> bool:
    values: dict[str, str] = {}
    for child in series_key_el:
        if _local_tag(child) != "Value":
            continue
        concept = child.attrib.get("concept")
        if concept:
            values[concept] = _normalize_text(child.attrib.get("value", ""))
    return all(values.get(key) == _normalize_text(val) for key, val in expected.items())


def _iter_series(root: ET.Element) -> list[ET.Element]:
    series: list[ET.Element] = []
    for element in root.iter():
        if _local_tag(element) == "Series":
            series.append(element)
    return series


def _find_child(parent: ET.Element, tag_name: str) -> ET.Element | None:
    for child in parent:
        if _local_tag(child) == tag_name:
            return child
    return None


def _find_children(parent: ET.Element, tag_name: str) -> list[ET.Element]:
    return [child for child in parent if _local_tag(child) == tag_name]


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
    matched_series = 0
    for series_el in _iter_series(root):
        key_el = _find_child(series_el, "SeriesKey")
        if key_el is None or not _series_matches(key_el, series_key):
            continue
        matched_series += 1

        period_text = ""
        attrs_el = _find_child(series_el, "Attributes")
        if attrs_el is not None:
            for attr in _find_children(attrs_el, "Value"):
                if attr.attrib.get("concept") == "PERIOD":
                    period_text = attr.attrib.get("value", "")
                    break

        month = _parse_month_period(period_text)
        if month is None:
            continue

        for obs_el in _find_children(series_el, "Obs"):
            time_el = _find_child(obs_el, "Time")
            value_el = _find_child(obs_el, "ObsValue")
            if time_el is None or value_el is None:
                continue
            try:
                year = int((time_el.text or "").strip())
            except ValueError:
                continue
            observed = date(year, month, 1)
            if observed < from_date.replace(day=1) or observed > to_date.replace(day=1):
                continue
            raw_value = _parse_decimal(value_el.attrib.get("value", ""))
            if raw_value is None:
                continue
            points.append((observed, _transform_value(raw_value, transform)))

    series = sorted(points, key=lambda item: item[0])
    if not series:
        logger.warning(
            "fedstat_series_empty",
            matched_series=matched_series,
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
        )
        raise RosstatError("Не удалось извлечь ряд из fedstat SDMX", code="rosstat_parse_error")
    return series


async def fetch_fedstat_sdmx(
    indicator_id: str,
    *,
    year: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> str:
    params: dict[str, str] = {"format": "sdmx", "id": indicator_id}
    post_data: dict[str, str] = {"id": indicator_id}
    if year is not None:
        post_data["Year"] = str(year)
        params["Year"] = str(year)
    elif from_date is not None and to_date is not None:
        params["startPeriod"] = str(from_date.year)
        params["endPeriod"] = str(to_date.year)
        post_data["startPeriod"] = str(from_date.year)
        post_data["endPeriod"] = str(to_date.year)

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
                    params=params,
                    data=post_data,
                )
            if response.status_code >= 400:
                errors.append(f"HTTP {response.status_code}")
                break
            text = response.content.decode("utf-8", errors="replace")
            if "<GenericData" not in text:
                errors.append("ответ не SDMX")
                break
            logger.info(
                "fedstat_http_post_ok",
                indicator_id=indicator_id,
                year=year,
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
    if from_date.year == to_date.year:
        xml_text = await fetch_fedstat_sdmx(
            indicator_id,
            year=from_date.year,
            from_date=from_date,
            to_date=to_date,
        )
        return parse_fedstat_sdmx_series(
            xml_text,
            series_key=series_key,
            transform=transform,
            from_date=from_date,
            to_date=to_date,
        )

    chunks: list[list[tuple[date, Decimal]]] = []
    for year in range(from_date.year, to_date.year + 1):
        year_from = max(from_date, date(year, 1, 1))
        year_to = min(to_date, date(year, 12, 31))
        try:
            xml_text = await fetch_fedstat_sdmx(indicator_id, year=year)
            chunk = parse_fedstat_sdmx_series(
                xml_text,
                series_key=series_key,
                transform=transform,
                from_date=year_from,
                to_date=year_to,
            )
            if chunk:
                chunks.append(chunk)
        except RosstatError as exc:
            logger.warning(
                "fedstat_year_fetch_failed",
                indicator_id=indicator_id,
                year=year,
                error=exc.message,
            )

    series = merge_series(chunks)
    if not series:
        raise RosstatError("Не удалось извлечь ряд из fedstat SDMX", code="rosstat_parse_error")
    return series


def merge_series(chunks: Iterable[list[tuple[date, Decimal]]]) -> list[tuple[date, Decimal]]:
    merged: dict[date, Decimal] = {}
    for chunk in chunks:
        for observed, value in chunk:
            merged[observed] = value
    return sorted(merged.items(), key=lambda item: item[0])
