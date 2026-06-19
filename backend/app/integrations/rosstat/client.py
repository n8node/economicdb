from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import httpx
import structlog

logger = structlog.get_logger()

CBR_INFLATION_URLS = (
    "http://www.cbr.ru/hd_base/infl/",
    "https://www.cbr.ru/hd_base/infl/",
)
DEFAULT_FROM_DATE = date(2020, 1, 1)
HTTP_HEADERS = {
    "User-Agent": "economicdb/0.1 (+https://economicdb.com)",
    "Accept": "text/html,application/xhtml+xml,*/*",
}
HTTP_TIMEOUT = 45.0


class RosstatError(Exception):
    def __init__(self, message: str, *, code: str = "rosstat_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _format_cbr_date_dot(value: date) -> str:
    return value.strftime("%d.%m.%Y")


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


async def _http_get(urls: tuple[str, ...], params: dict[str, str] | None = None) -> str:
    errors: list[str] = []
    for url in urls:
        try:
            async with httpx.AsyncClient(
                timeout=HTTP_TIMEOUT,
                follow_redirects=True,
                headers=HTTP_HEADERS,
            ) as client:
                response = await client.get(url, params=params)
            if response.status_code >= 400:
                errors.append(f"{url}: HTTP {response.status_code}")
                continue
            logger.info("rosstat_http_get_ok", url=url)
            return response.text
        except httpx.TimeoutException:
            errors.append(f"{url}: timeout")
            logger.warning("rosstat_http_get_timeout", url=url)
        except httpx.HTTPError as exc:
            errors.append(f"{url}: {exc}")
            logger.warning("rosstat_http_get_failed", url=url, error=str(exc))
    if any("timeout" in item for item in errors):
        raise RosstatError("Росстат/ЦБ не ответил за 45 секунд", code="rosstat_timeout")
    raise RosstatError(f"Не удалось подключиться к Росстату ({'; '.join(errors)})", code="rosstat_network_error")


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


async def fetch_cpi_yoy_series(
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    end = to_date or datetime.now(timezone.utc).date()
    html = await _http_get(
        CBR_INFLATION_URLS,
        {
            "UniDbQuery.Posted": "True",
            "UniDbQuery.From": _format_cbr_date_dot(from_date),
            "UniDbQuery.To": _format_cbr_date_dot(end),
        },
    )
    series = _parse_cpi_yoy_html(html)
    if not series:
        raise RosstatError("Не удалось разобрать ИПЦ России (г/г)", code="rosstat_parse_error")
    logger.info(
        "rosstat_cpi_yoy_loaded",
        points=len(series),
        from_date=from_date.isoformat(),
        to_date=end.isoformat(),
    )
    return series


async def test_connection() -> dict:
    today = datetime.now(timezone.utc).date()
    from_date = today - timedelta(days=400)
    series = await fetch_cpi_yoy_series(from_date=from_date, to_date=today)
    observed, value = series[-1]
    return {
        "cpi_yoy_latest": {
            "date": observed.isoformat(),
            "value": str(value),
        },
    }
