from __future__ import annotations

import asyncio
import csv
import io
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Iterator

import httpx
import structlog

logger = structlog.get_logger()

OECD_SDMX_BASE = "https://sdmx.oecd.org/public/rest/data"
OECD_DATAFLOWS = {
    "HICP": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_HICP,1.0",
    "CLI": "OECD.SDD.STES,DSD_STES@DF_CLI,4.1",
    "BTS": "OECD.SDD.STES,DSD_STES@DF_BTS,4.0",
}
DEFAULT_FROM_DATE = date(2020, 1, 1)
HTTP_HEADERS = {
    "User-Agent": "economicdb/0.1 (+https://economicdb.com)",
    "Accept": "text/csv,*/*",
}
HTTP_TIMEOUT = httpx.Timeout(connect=8.0, read=45.0, write=10.0, pool=10.0)
HTTP_RETRIES = 3
MONTH_PERIOD_RE = re.compile(r"^(\d{4})-(\d{2})$")
QUARTER_PERIOD_RE = re.compile(r"^(\d{4})-Q([1-4])$")


class OecdError(Exception):
    def __init__(self, message: str, *, code: str = "oecd_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def parse_oecd_external_id(external_id: str) -> tuple[str, str]:
    if "/" in external_id:
        flow_key, series_key = external_id.split("/", 1)
        dataflow = OECD_DATAFLOWS.get(flow_key)
        if dataflow is None or not series_key:
            raise OecdError(f"Неизвестный OECD dataflow: {external_id}", code="oecd_unknown_external_id")
        return dataflow, series_key
    return OECD_DATAFLOWS["HICP"], external_id


def _iter_year_chunks(from_date: date, to_date: date) -> Iterator[tuple[date, date]]:
    cursor = from_date
    while cursor <= to_date:
        chunk_end = min(date(cursor.year, 12, 31), to_date)
        yield cursor, chunk_end
        if chunk_end >= to_date:
            break
        cursor = date(cursor.year + 1, 1, 1)


def _format_period(value: date) -> str:
    return value.strftime("%Y-%m")


def _parse_period(raw: str) -> date | None:
    cleaned = raw.strip()
    month_match = MONTH_PERIOD_RE.match(cleaned)
    if month_match:
        year = int(month_match.group(1))
        month = int(month_match.group(2))
        if 1 <= month <= 12:
            return date(year, month, 1)
    quarter_match = QUARTER_PERIOD_RE.match(cleaned)
    if quarter_match:
        year = int(quarter_match.group(1))
        quarter = int(quarter_match.group(2))
        return date(year, (quarter - 1) * 3 + 1, 1)
    return None


def _parse_decimal(raw: str) -> Decimal | None:
    cleaned = raw.strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except Exception:
        return None


def _build_data_url(dataflow: str, series_key: str, *, start_period: str, end_period: str) -> str:
    return (
        f"{OECD_SDMX_BASE}/{dataflow}/{series_key}"
        f"?startPeriod={start_period}&endPeriod={end_period}"
        "&dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
    )


def _parse_sdmx_csv(text: str) -> list[tuple[date, Decimal]]:
    reader = csv.DictReader(io.StringIO(text))
    points: list[tuple[date, Decimal]] = []
    for row in reader:
        if row.get("STRUCTURE") != "DATAFLOW":
            continue
        observed = _parse_period(row.get("TIME_PERIOD", ""))
        value = _parse_decimal(row.get("OBS_VALUE", ""))
        if observed is None or value is None:
            continue
        points.append((observed, value))
    return sorted(points, key=lambda item: item[0])


async def _http_get(url: str) -> str:
    errors: list[str] = []
    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            async with httpx.AsyncClient(
                timeout=HTTP_TIMEOUT,
                follow_redirects=True,
                headers=HTTP_HEADERS,
                trust_env=False,
            ) as client:
                response = await client.get(url)
            if response.status_code == 404 and response.text.strip() in {"NoRecordsFound", "NoResultsFound"}:
                return ""
            if response.status_code >= 400:
                errors.append(f"HTTP {response.status_code}: {response.text[:200]}")
                break
            logger.info("oecd_http_get_ok", url=url, attempt=attempt, bytes=len(response.content))
            return response.text
        except httpx.TimeoutException:
            errors.append(f"timeout (attempt {attempt})")
            logger.warning("oecd_http_get_timeout", url=url, attempt=attempt)
            if attempt < HTTP_RETRIES:
                await asyncio.sleep(attempt)
        except httpx.HTTPError as exc:
            errors.append(str(exc))
            logger.warning("oecd_http_get_failed", url=url, error=str(exc), attempt=attempt)
            break
    if any("timeout" in item for item in errors):
        raise OecdError("OECD SDMX не ответил вовремя", code="oecd_timeout")
    raise OecdError(f"Не удалось загрузить OECD SDMX ({'; '.join(errors)})", code="oecd_network_error")


async def fetch_sdmx_series(
    external_id: str,
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    dataflow, series_key = parse_oecd_external_id(external_id)
    end = to_date or datetime.now(timezone.utc).date()
    merged: dict[date, Decimal] = {}
    for chunk_from, chunk_to in _iter_year_chunks(from_date, end):
        url = _build_data_url(
            dataflow,
            series_key,
            start_period=_format_period(chunk_from),
            end_period=_format_period(chunk_to),
        )
        csv_text = await _http_get(url)
        if not csv_text:
            continue
        for observed, value in _parse_sdmx_csv(csv_text):
            merged[observed] = value

    series = sorted(merged.items(), key=lambda item: item[0])
    if not series:
        raise OecdError(f"Не удалось получить ряд OECD ({external_id})", code="oecd_parse_error")
    logger.info(
        "oecd_series_loaded",
        external_id=external_id,
        points=len(series),
        from_date=from_date.isoformat(),
        to_date=end.isoformat(),
    )
    return series


async def fetch_hicp_yoy_series(
    series_key: str,
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    return await fetch_sdmx_series(series_key, from_date=from_date, to_date=to_date)


async def test_connection() -> dict:
    series_key = "EA20.M.HICP.CPI.PA._T.N.GY"
    today = datetime.now(timezone.utc).date()
    from_date = date(today.year - 1, today.month, 1)
    series = await fetch_hicp_yoy_series(series_key, from_date=from_date, to_date=today)
    observed, value = series[-1]
    return {
        "hicp_yoy_latest": {
            "series_key": series_key,
            "date": observed.isoformat(),
            "value": str(value),
        },
    }
