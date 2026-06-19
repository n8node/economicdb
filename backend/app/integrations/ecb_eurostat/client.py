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

ECB_DATA_API_BASE = "https://data-api.ecb.europa.eu/service/data"
EUROSTAT_SDMX_BASE = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data"
DEFAULT_FROM_DATE = date(2020, 1, 1)
HTTP_HEADERS = {
    "User-Agent": "economicdb/0.1 (+https://economicdb.com)",
    "Accept": "text/csv,text/plain,*/*",
}
HTTP_TIMEOUT = httpx.Timeout(connect=8.0, read=60.0, write=10.0, pool=10.0)
HTTP_RETRIES = 3
MONTH_PERIOD_RE = re.compile(r"^(\d{4})-(\d{2})$")


class EcbEurostatError(Exception):
    def __init__(self, message: str, *, code: str = "ecb_eurostat_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


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


def _parse_month_period(raw: str) -> date | None:
    match = MONTH_PERIOD_RE.match(raw.strip())
    if not match:
        return None
    year = int(match.group(1))
    month = int(match.group(2))
    if month < 1 or month > 12:
        return None
    return date(year, month, 1)


def _parse_decimal(raw: str) -> Decimal | None:
    cleaned = raw.strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except Exception:
        return None


def _parse_day_period(raw: str) -> date | None:
    cleaned = raw.strip()
    if not cleaned:
        return None
    try:
        return date.fromisoformat(cleaned[:10])
    except ValueError:
        return None


def _aggregate_daily_to_monthly(points: list[tuple[date, Decimal]]) -> list[tuple[date, Decimal]]:
    by_month: dict[date, tuple[date, Decimal]] = {}
    for observed, value in sorted(points, key=lambda item: item[0]):
        month_start = date(observed.year, observed.month, 1)
        current = by_month.get(month_start)
        if current is None or observed >= current[0]:
            by_month[month_start] = (observed, value)
    return sorted((month_start, value) for month_start, (_, value) in by_month.items())


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
            if response.status_code >= 400:
                errors.append(f"HTTP {response.status_code}: {response.text[:200]}")
                break
            logger.info("ecb_eurostat_http_get_ok", url=url, attempt=attempt, bytes=len(response.content))
            return response.text
        except httpx.TimeoutException:
            errors.append(f"timeout (attempt {attempt})")
            if attempt < HTTP_RETRIES:
                await asyncio.sleep(attempt)
        except httpx.HTTPError as exc:
            errors.append(str(exc))
            break
    if any("timeout" in item for item in errors):
        raise EcbEurostatError("ECB/Eurostat не ответил вовремя", code="ecb_eurostat_timeout")
    raise EcbEurostatError(
        f"Не удалось загрузить ECB/Eurostat ({'; '.join(errors)})",
        code="ecb_eurostat_network_error",
    )


def _parse_eurostat_csv(text: str) -> list[tuple[date, Decimal]]:
    reader = csv.DictReader(io.StringIO(text))
    points: list[tuple[date, Decimal]] = []
    for row in reader:
        observed = _parse_month_period(row.get("TIME_PERIOD", ""))
        value = _parse_decimal(row.get("OBS_VALUE", ""))
        if observed is None or value is None:
            continue
        points.append((observed, value))
    return sorted(points, key=lambda item: item[0])


def _parse_ecb_csv(text: str) -> list[tuple[date, Decimal]]:
    reader = csv.DictReader(io.StringIO(text))
    points: list[tuple[date, Decimal]] = []
    for row in reader:
        observed = _parse_day_period(row.get("TIME_PERIOD", ""))
        value = _parse_decimal(row.get("OBS_VALUE", ""))
        if observed is None or value is None:
            continue
        points.append((observed, value))
    return points


async def fetch_ecb_deposit_rate_series(
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    end = to_date or datetime.now(timezone.utc).date()
    merged: dict[date, Decimal] = {}
    for chunk_from, chunk_to in _iter_year_chunks(from_date, end):
        url = (
            f"{ECB_DATA_API_BASE}/FM/D.U2.EUR.4F.KR.DFR.LEV"
            f"?startPeriod={chunk_from.isoformat()}&endPeriod={chunk_to.isoformat()}&format=csvdata"
        )
        csv_text = await _http_get(url)
        for observed, value in _aggregate_daily_to_monthly(_parse_ecb_csv(csv_text)):
            if observed < from_date.replace(day=1) or observed > end:
                continue
            merged[observed] = value
    series = sorted(merged.items(), key=lambda item: item[0])
    if not series:
        raise EcbEurostatError("Не удалось получить ставку ECB", code="ecb_eurostat_parse_error")
    logger.info("ecb_deposit_rate_loaded", points=len(series))
    return series


async def fetch_eurostat_hicp_yoy_series(
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    end = to_date or datetime.now(timezone.utc).date()
    merged: dict[date, Decimal] = {}
    for chunk_from, chunk_to in _iter_year_chunks(from_date, end):
        url = (
            f"{EUROSTAT_SDMX_BASE}/PRC_HICP_MANR/M.RCH_A.CP00.EA20"
            f"?format=SDMX-CSV&startPeriod={_format_period(chunk_from)}&endPeriod={_format_period(chunk_to)}"
        )
        csv_text = await _http_get(url)
        for observed, value in _parse_eurostat_csv(csv_text):
            merged[observed] = value
    series = sorted(merged.items(), key=lambda item: item[0])
    if not series:
        raise EcbEurostatError("Не удалось получить HICP Eurostat", code="ecb_eurostat_parse_error")
    logger.info("eurostat_hicp_yoy_loaded", points=len(series))
    return series


async def test_connection() -> dict:
    today = datetime.now(timezone.utc).date()
    from_date = date(today.year - 1, today.month, 1)
    deposit = await fetch_ecb_deposit_rate_series(from_date=from_date, to_date=today)
    hicp = await fetch_eurostat_hicp_yoy_series(from_date=from_date, to_date=today)
    dep_date, dep_value = deposit[-1]
    hicp_date, hicp_value = hicp[-1]
    return {
        "key_rate_latest": {
            "date": dep_date.isoformat(),
            "value": str(dep_value),
        },
        "hicp_yoy_latest": {
            "date": hicp_date.isoformat(),
            "value": str(hicp_value),
        },
    }
