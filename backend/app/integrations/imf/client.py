from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

import httpx
import structlog

logger = structlog.get_logger()

IMF_DATAMAPPER_BASE = "https://www.imf.org/external/datamapper/api/v1"
DEFAULT_FROM_DATE = date(2020, 1, 1)
HTTP_HEADERS = {
    "User-Agent": "economicdb/0.1 (+https://economicdb.com)",
    "Accept": "application/json,*/*",
}
HTTP_TIMEOUT = httpx.Timeout(connect=8.0, read=60.0, write=10.0, pool=10.0)
HTTP_RETRIES = 3


class ImfError(Exception):
    def __init__(self, message: str, *, code: str = "imf_error") -> None:
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
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _build_periods(from_date: date, to_date: date) -> str:
    return ",".join(str(year) for year in range(from_date.year, to_date.year + 1))


def _build_url(indicator_code: str, country_code: str, *, from_date: date, to_date: date) -> str:
    periods = _build_periods(from_date, to_date)
    return f"{IMF_DATAMAPPER_BASE}/{indicator_code}/{country_code}?periods={periods}"


def _parse_datamapper_json(
    payload: dict,
    *,
    indicator_code: str,
    country_code: str,
    from_date: date,
    to_date: date,
) -> list[tuple[date, Decimal]]:
    values_root = payload.get("values")
    if not isinstance(values_root, dict):
        raise ImfError("Некорректный ответ IMF DataMapper", code="imf_parse_error")

    indicator_values = values_root.get(indicator_code)
    if not isinstance(indicator_values, dict):
        raise ImfError(f"Показатель IMF не найден: {indicator_code}", code="imf_parse_error")

    country_values = indicator_values.get(country_code)
    if not isinstance(country_values, dict):
        raise ImfError(f"Страна IMF не найдена: {country_code}", code="imf_parse_error")

    points: list[tuple[date, Decimal]] = []
    for year_text, raw_value in country_values.items():
        try:
            year = int(str(year_text))
        except ValueError:
            continue
        if year < from_date.year or year > to_date.year:
            continue
        value = _parse_decimal(raw_value)
        if value is None:
            continue
        points.append((date(year, 1, 1), value))

    return sorted(points, key=lambda item: item[0])


async def _http_get_json(url: str) -> dict:
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
            if not isinstance(payload, dict):
                raise ImfError("Некорректный JSON IMF DataMapper", code="imf_parse_error")
            logger.info("imf_http_get_ok", url=url, attempt=attempt, bytes=len(response.content))
            return payload
        except httpx.TimeoutException:
            errors.append(f"timeout (attempt {attempt})")
            logger.warning("imf_http_get_timeout", url=url, attempt=attempt)
            if attempt < HTTP_RETRIES:
                await asyncio.sleep(attempt)
        except httpx.HTTPError as exc:
            errors.append(str(exc))
            logger.warning("imf_http_get_failed", url=url, error=str(exc), attempt=attempt)
            break
        except ValueError as exc:
            errors.append(f"invalid json: {exc}")
            break
    if any("timeout" in item for item in errors):
        raise ImfError("IMF DataMapper не ответил вовремя", code="imf_timeout")
    raise ImfError(f"Не удалось загрузить IMF DataMapper ({'; '.join(errors)})", code="imf_network_error")


async def fetch_gdp_yoy_series(
    indicator_code: str,
    country_code: str,
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    end = to_date or datetime.now(timezone.utc).date()
    url = _build_url(indicator_code, country_code, from_date=from_date, to_date=end)
    payload = await _http_get_json(url)
    series = _parse_datamapper_json(
        payload,
        indicator_code=indicator_code,
        country_code=country_code,
        from_date=from_date,
        to_date=end,
    )
    if not series:
        raise ImfError("Не удалось получить ряд IMF", code="imf_parse_error")
    logger.info(
        "imf_gdp_yoy_loaded",
        indicator_code=indicator_code,
        country_code=country_code,
        points=len(series),
        from_date=from_date.isoformat(),
        to_date=end.isoformat(),
    )
    return series


async def test_connection() -> dict:
    indicator_code = "NGDP_RPCH"
    country_code = "CHN"
    today = datetime.now(timezone.utc).date()
    from_date = date(today.year - 3, 1, 1)
    series = await fetch_gdp_yoy_series(indicator_code, country_code, from_date=from_date, to_date=today)
    observed, value = series[-1]
    return {
        "gdp_yoy_latest": {
            "indicator_code": indicator_code,
            "country_code": country_code,
            "date": observed.isoformat(),
            "value": str(value),
        },
    }
