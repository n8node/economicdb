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
QUARTER_PERIOD_RE = re.compile(r"^(\d{4})-Q([1-4])$")


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


def _parse_quarter_period(raw: str) -> date | None:
    match = QUARTER_PERIOD_RE.match(raw.strip())
    if not match:
        return None
    year = int(match.group(1))
    quarter = int(match.group(2))
    month = (quarter - 1) * 3 + 1
    return date(year, month, 1)


def _parse_eurostat_period(raw: str) -> date | None:
    return _parse_quarter_period(raw) or _parse_month_period(raw)


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


def _latest_eurostat_month_end(end: date) -> date:
    """Eurostat rejects endPeriod for months without published HICP yet."""
    today = datetime.now(timezone.utc).date()
    latest = date(today.year, today.month, 1)
    if today.month == 1:
        latest = date(today.year - 1, 12, 1)
    else:
        latest = date(today.year, today.month - 1, 1)
    capped = date(end.year, end.month, 1)
    return min(capped, latest)


async def _http_get(url: str, *, allow_client_error: bool = False) -> str | None:
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
                detail = response.text[:200]
                if allow_client_error and 400 <= response.status_code < 500:
                    logger.warning(
                        "ecb_eurostat_http_client_error",
                        url=url,
                        status_code=response.status_code,
                        detail=detail,
                    )
                    return None
                errors.append(f"HTTP {response.status_code}: {detail}")
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
        observed = _parse_eurostat_period(row.get("TIME_PERIOD", ""))
        value = _parse_decimal(row.get("OBS_VALUE", ""))
        if observed is None or value is None:
            continue
        points.append((observed, value))
    return sorted(points, key=lambda item: item[0])


def _split_eurostat_external_id(external_id: str) -> tuple[str, str]:
    cleaned = external_id.strip().lstrip("/")
    if "/" not in cleaned:
        raise EcbEurostatError(
            f"Неверный Eurostat external_id: {external_id}",
            code="ecb_eurostat_bad_external_id",
        )
    dataset, key = cleaned.split("/", 1)
    return dataset.strip(), key.strip()


def _format_eurostat_end_period(end: date, *, quarterly: bool) -> str:
    if quarterly:
        quarter = (end.month - 1) // 3 + 1
        return f"{end.year}-Q{quarter}"
    return _format_period(end)


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


async def fetch_ecb_series_by_key(
    series_key: str,
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    end = to_date or datetime.now(timezone.utc).date()
    merged: dict[date, Decimal] = {}
    for chunk_from, chunk_to in _iter_year_chunks(from_date, end):
        url = (
            f"{ECB_DATA_API_BASE}/{series_key.lstrip('/')}"
            f"?startPeriod={chunk_from.isoformat()}&endPeriod={chunk_to.isoformat()}&format=csvdata"
        )
        csv_text = await _http_get(url)
        if csv_text is None:
            continue
        for observed, value in _aggregate_daily_to_monthly(_parse_ecb_csv(csv_text)):
            if observed < from_date.replace(day=1) or observed > end:
                continue
            merged[observed] = value
    series = sorted(merged.items(), key=lambda item: item[0])
    if not series:
        raise EcbEurostatError(f"Не удалось получить ряд ECB {series_key}", code="ecb_eurostat_parse_error")
    return series


async def fetch_eurostat_series_by_key(
    dataset_key: str,
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    dataset, key = _split_eurostat_external_id(dataset_key)
    quarterly = key.startswith("Q.") or ".Q." in key or dataset.lower().startswith("namq")
    end = _latest_eurostat_month_end(to_date or datetime.now(timezone.utc).date())
    if from_date > end:
        from_date = date(end.year - 1, end.month, 1)
    merged: dict[date, Decimal] = {}
    for chunk_from, chunk_to in _iter_year_chunks(from_date, end):
        chunk_end = _latest_eurostat_month_end(chunk_to)
        if chunk_from > chunk_end:
            continue
        start_period = _format_eurostat_end_period(chunk_from, quarterly=quarterly) if quarterly else _format_period(chunk_from)
        end_period = _format_eurostat_end_period(chunk_end, quarterly=quarterly)
        url = (
            f"{EUROSTAT_SDMX_BASE}/{dataset}/{key}"
            f"?format=SDMX-CSV&startPeriod={start_period}&endPeriod={end_period}"
        )
        csv_text = await _http_get(url, allow_client_error=True)
        if csv_text is None:
            continue
        for observed, value in _parse_eurostat_csv(csv_text):
            merged[observed] = value
    series = sorted(merged.items(), key=lambda item: item[0])
    if not series:
        raise EcbEurostatError(f"Не удалось получить ряд Eurostat {dataset_key}", code="ecb_eurostat_parse_error")
    return series


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
        if csv_text is None:
            continue
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
    end = _latest_eurostat_month_end(to_date or datetime.now(timezone.utc).date())
    if from_date > end:
        from_date = date(end.year - 1, end.month, 1)
    merged: dict[date, Decimal] = {}
    for chunk_from, chunk_to in _iter_year_chunks(from_date, end):
        chunk_end = _latest_eurostat_month_end(chunk_to)
        if chunk_from > chunk_end:
            continue
        url = (
            f"{EUROSTAT_SDMX_BASE}/PRC_HICP_MANR/M.RCH_A.CP00.EA20"
            f"?format=SDMX-CSV&startPeriod={_format_period(chunk_from)}&endPeriod={_format_period(chunk_end)}"
        )
        csv_text = await _http_get(url, allow_client_error=True)
        if csv_text is None:
            continue
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
