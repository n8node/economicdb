from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

import httpx
import structlog

logger = structlog.get_logger()

WORLD_BANK_API_BASE = "https://api.worldbank.org/v2"
DEFAULT_FROM_DATE = date(2000, 1, 1)
HTTP_HEADERS = {
    "User-Agent": "economicdb/0.1 (+https://economicdb.com)",
    "Accept": "application/json,*/*",
}
HTTP_TIMEOUT = httpx.Timeout(connect=8.0, read=60.0, write=10.0, pool=10.0)
HTTP_RETRIES = 3


class WorldBankError(Exception):
    def __init__(self, message: str, *, code: str = "world_bank_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _parse_decimal(raw: object) -> Decimal | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return Decimal(str(raw))
    cleaned = str(raw).strip()
    if not cleaned or cleaned.lower() in {"null", "nan", "n/a"}:
        return None
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def _build_url(country_code: str, indicator_code: str, *, from_date: date, to_date: date) -> str:
    date_range = f"{from_date.year}:{to_date.year}"
    return (
        f"{WORLD_BANK_API_BASE}/country/{country_code}/indicator/{indicator_code}"
        f"?format=json&date={date_range}&per_page=20000"
    )


def _parse_world_bank_json(
    payload: list,
    *,
    from_date: date,
    to_date: date,
) -> list[tuple[date, Decimal]]:
    if len(payload) < 2 or not isinstance(payload[1], list):
        raise WorldBankError("Некорректный ответ World Bank API", code="world_bank_parse_error")

    points: list[tuple[date, Decimal]] = []
    for row in payload[1]:
        if not isinstance(row, dict):
            continue
        try:
            year = int(str(row.get("date", "")))
        except ValueError:
            continue
        if year < from_date.year or year > to_date.year:
            continue
        value = _parse_decimal(row.get("value"))
        if value is None:
            continue
        points.append((date(year, 1, 1), value))

    return sorted(points, key=lambda item: item[0])


async def _http_get_json(url: str) -> list:
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
            payload = response.json()
            if not isinstance(payload, list):
                raise WorldBankError("Некорректный JSON World Bank", code="world_bank_parse_error")
            logger.info("world_bank_http_get_ok", url=url, attempt=attempt, bytes=len(response.content))
            return payload
        except httpx.TimeoutException:
            errors.append(f"timeout (attempt {attempt})")
            if attempt < HTTP_RETRIES:
                await asyncio.sleep(attempt)
        except httpx.HTTPError as exc:
            errors.append(str(exc))
            break
        except ValueError as exc:
            errors.append(f"invalid json: {exc}")
            break
    if any("timeout" in item for item in errors):
        raise WorldBankError("World Bank API не ответил вовремя", code="world_bank_timeout")
    raise WorldBankError(
        f"Не удалось загрузить World Bank API ({'; '.join(errors)})",
        code="world_bank_network_error",
    )


async def fetch_indicator_series(
    country_code: str,
    indicator_code: str,
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    end = to_date or datetime.now(timezone.utc).date()
    url = _build_url(country_code, indicator_code, from_date=from_date, to_date=end)
    payload = await _http_get_json(url)
    series = _parse_world_bank_json(payload, from_date=from_date, to_date=end)
    if not series:
        raise WorldBankError("Не удалось получить ряд World Bank", code="world_bank_parse_error")
    logger.info(
        "world_bank_series_loaded",
        country_code=country_code,
        indicator_code=indicator_code,
        points=len(series),
        from_date=from_date.isoformat(),
        to_date=end.isoformat(),
    )
    return series


async def test_connection() -> dict:
    country_code = "RU"
    indicator_code = "NY.GDP.MKTP.KD.ZG"
    today = datetime.now(timezone.utc).date()
    from_date = date(today.year - 5, 1, 1)
    series = await fetch_indicator_series(
        country_code,
        indicator_code,
        from_date=from_date,
        to_date=today,
    )
    observed, value = series[-1]
    return {
        "gdp_yoy_latest": {
            "date": observed.isoformat(),
            "value": str(value),
        },
    }
