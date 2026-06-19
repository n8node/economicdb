from __future__ import annotations

import asyncio
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Iterator

import httpx
import structlog

from app.integrations.rosstat.mappings import ROSSTAT_MAPPINGS

logger = structlog.get_logger()

CBR_INFLATION_URLS = (
    "https://www.cbr.ru/hd_base/infl/",
    "http://www.cbr.ru/hd_base/infl/",
)
DEFAULT_FROM_DATE = date(2020, 1, 1)
HTTP_HEADERS = {
    "User-Agent": "economicdb/0.1 (+https://economicdb.com)",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://www.cbr.ru/hd_base/infl/",
}
HTTP_TIMEOUT = httpx.Timeout(connect=8.0, read=30.0, write=10.0, pool=10.0)
HTTP_RETRIES = 3


class RosstatError(Exception):
    def __init__(self, message: str, *, code: str = "rosstat_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _format_cbr_date_dot(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def _iter_year_chunks(from_date: date, to_date: date) -> Iterator[tuple[date, date]]:
    cursor = from_date
    while cursor <= to_date:
        chunk_end = min(date(cursor.year, 12, 31), to_date)
        yield cursor, chunk_end
        if chunk_end >= to_date:
            break
        cursor = date(cursor.year + 1, 1, 1)


def _parse_decimal(raw: str) -> Decimal | None:
    cleaned = raw.strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except Exception:
        return None


def _parse_month_year(value: str) -> date | None:
    value = value.strip()
    if not value or "." not in value:
        return None
    month_text, year_text = value.split(".", 1)
    try:
        month = int(month_text)
        year = int(year_text)
        if month < 1 or month > 12:
            return None
        return date(year, month, 1)
    except ValueError:
        return None


def _parse_cpi_yoy_html(html: str) -> list[tuple[date, Decimal]]:
    points: list[tuple[date, Decimal]] = []
    for match in re.finditer(
        r"<td[^>]*>\s*(\d{2}\.\d{4})\s*</td>\s*"
        r"<td[^>]*>[\d,\.\s]+</td>\s*"
        r"<td[^>]*>\s*([\d,\.]+)\s*</td>",
        html,
        flags=re.IGNORECASE,
    ):
        observed = _parse_month_year(match.group(1))
        value = _parse_decimal(match.group(2))
        if observed is None or value is None:
            continue
        points.append((observed, value))
    return sorted(points, key=lambda item: item[0])


async def _http_get(urls: tuple[str, ...], params: dict[str, str] | None = None) -> str:
    errors: list[str] = []
    for url in urls:
        for attempt in range(1, HTTP_RETRIES + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=HTTP_TIMEOUT,
                    follow_redirects=True,
                    headers=HTTP_HEADERS,
                    trust_env=False,
                ) as client:
                    response = await client.get(url, params=params)
                if response.status_code >= 400:
                    errors.append(f"{url}: HTTP {response.status_code}")
                    break
                logger.info("rosstat_http_get_ok", url=url, attempt=attempt)
                return response.text
            except httpx.TimeoutException:
                errors.append(f"{url}: timeout (attempt {attempt})")
                logger.warning("rosstat_http_get_timeout", url=url, attempt=attempt)
                if attempt < HTTP_RETRIES:
                    await asyncio.sleep(attempt)
            except httpx.HTTPError as exc:
                errors.append(f"{url}: {exc}")
                logger.warning("rosstat_http_get_failed", url=url, error=str(exc), attempt=attempt)
                break
    if any("timeout" in item for item in errors):
        raise RosstatError("Росстат/ЦБ не ответил вовремя", code="rosstat_timeout")
    raise RosstatError(f"Не удалось загрузить ИПЦ ({'; '.join(errors)})", code="rosstat_network_error")


async def _fetch_cpi_yoy_chunk(from_date: date, to_date: date) -> list[tuple[date, Decimal]]:
    html = await _http_get(
        CBR_INFLATION_URLS,
        {
            "UniDbQuery.Posted": "True",
            "UniDbQuery.From": _format_cbr_date_dot(from_date),
            "UniDbQuery.To": _format_cbr_date_dot(to_date),
        },
    )
    series = _parse_cpi_yoy_html(html)
    if not series:
        raise RosstatError(
            f"Не удалось разобрать ИПЦ за {from_date.isoformat()}–{to_date.isoformat()}",
            code="rosstat_parse_error",
        )
    return series


async def fetch_cpi_yoy_from_cbr(
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    end = to_date or datetime.now(timezone.utc).date()
    merged: dict[date, Decimal] = {}
    for chunk_from, chunk_to in _iter_year_chunks(from_date, end):
        for observed, value in await _fetch_cpi_yoy_chunk(chunk_from, chunk_to):
            merged[observed] = value
    series = sorted(merged.items(), key=lambda item: item[0])
    if not series:
        raise RosstatError("Не удалось получить ИПЦ России (г/г)", code="rosstat_parse_error")
    logger.info(
        "rosstat_cpi_yoy_loaded",
        source="cbr",
        points=len(series),
        from_date=from_date.isoformat(),
        to_date=end.isoformat(),
    )
    return series


async def fetch_cpi_yoy_series(
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    from app.integrations.rosstat.fedstat import fetch_fedstat_series

    end = to_date or datetime.now(timezone.utc).date()
    mapping = next(item for item in ROSSTAT_MAPPINGS if item.series_type == "cpi_yoy")
    try:
        series = await fetch_fedstat_series(
            mapping.fedstat_indicator_id or "",
            series_key=mapping.fedstat_series_key or {},
            transform=mapping.fedstat_transform,
            from_date=from_date,
            to_date=end,
        )
        logger.info(
            "rosstat_cpi_yoy_loaded",
            source="fedstat",
            points=len(series),
            from_date=from_date.isoformat(),
            to_date=end.isoformat(),
        )
        return series
    except RosstatError as exc:
        logger.warning("rosstat_cpi_yoy_fedstat_failed", error=exc.message)
    except Exception as exc:
        logger.warning("rosstat_cpi_yoy_fedstat_failed", error=str(exc))
    return await fetch_cpi_yoy_from_cbr(from_date=from_date, to_date=end)


async def fetch_industrial_yoy_series(
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    from app.integrations.rosstat.fedstat import fetch_fedstat_series

    end = to_date or datetime.now(timezone.utc).date()
    mapping = next(item for item in ROSSTAT_MAPPINGS if item.series_type == "industrial_yoy")
    series = await fetch_fedstat_series(
        mapping.fedstat_indicator_id or "",
        series_key=mapping.fedstat_series_key or {},
        transform=mapping.fedstat_transform,
        from_date=from_date,
        to_date=end,
    )
    logger.info(
        "rosstat_industrial_yoy_loaded",
        source="fedstat",
        points=len(series),
        from_date=from_date.isoformat(),
        to_date=end.isoformat(),
    )
    return series


async def test_connection() -> dict:
    today = datetime.now(timezone.utc).date()
    month_start = date(today.year, today.month, 1)
    from_date = month_start - timedelta(days=120)
    cpi_series = await fetch_cpi_yoy_series(from_date=from_date, to_date=today)
    industrial_series = await fetch_industrial_yoy_series(from_date=from_date, to_date=today)
    cpi_date, cpi_value = cpi_series[-1]
    ind_date, ind_value = industrial_series[-1]
    return {
        "cpi_yoy_latest": {
            "date": cpi_date.isoformat(),
            "value": str(cpi_value),
        },
        "industrial_yoy_latest": {
            "date": ind_date.isoformat(),
            "value": str(ind_value),
        },
    }
