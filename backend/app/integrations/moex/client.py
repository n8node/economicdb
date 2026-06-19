from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

import httpx
import structlog

logger = structlog.get_logger()

MOEX_ISS_BASE = "https://iss.moex.com/iss"
DEFAULT_FROM_DATE = date(2020, 1, 1)
HTTP_HEADERS = {
    "User-Agent": "economicdb/0.1 (+https://economicdb.com)",
    "Accept": "application/json,*/*",
}
HTTP_TIMEOUT = httpx.Timeout(connect=8.0, read=60.0, write=10.0, pool=10.0)
HTTP_RETRIES = 3
PAGE_SIZE = 100


class MoexError(Exception):
    def __init__(self, message: str, *, code: str = "moex_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _parse_decimal(raw: object) -> Decimal | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return Decimal(str(raw))
    cleaned = str(raw).strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def _parse_day(raw: str) -> date | None:
    try:
        return date.fromisoformat(raw.strip()[:10])
    except ValueError:
        return None


def _parse_history_page(
    payload: dict,
    *,
    value_column: str,
    from_date: date,
    to_date: date,
) -> tuple[list[tuple[date, Decimal]], int, int]:
    history = payload.get("history")
    if not isinstance(history, dict):
        raise MoexError("Некорректный ответ MOEX ISS", code="moex_parse_error")

    columns = history.get("columns")
    rows = history.get("data")
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise MoexError("Некорректная таблица history MOEX", code="moex_parse_error")

    try:
        date_idx = columns.index("TRADEDATE")
        value_idx = columns.index(value_column)
    except ValueError as exc:
        raise MoexError(f"Колонка MOEX не найдена: {exc}", code="moex_parse_error") from exc

    points: list[tuple[date, Decimal]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) <= max(date_idx, value_idx):
            continue
        observed = _parse_day(str(row[date_idx]))
        value = _parse_decimal(row[value_idx])
        if observed is None or value is None:
            continue
        if observed < from_date or observed > to_date:
            continue
        points.append((observed, value))

    cursor = payload.get("history.cursor", {})
    cursor_rows = cursor.get("data") if isinstance(cursor, dict) else None
    start = 0
    total = len(rows)
    if isinstance(cursor_rows, list) and cursor_rows and isinstance(cursor_rows[0], list):
        if len(cursor_rows[0]) >= 3:
            start = int(cursor_rows[0][0])
            total = int(cursor_rows[0][1])
    return points, start, total


async def _http_get_json(url: str, params: dict[str, str | int]) -> dict:
    errors: list[str] = []
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
                errors.append(f"HTTP {response.status_code}: {response.text[:200]}")
                break
            payload = response.json()
            if not isinstance(payload, dict):
                raise MoexError("Некорректный JSON MOEX ISS", code="moex_parse_error")
            logger.info("moex_http_get_ok", url=url, attempt=attempt, bytes=len(response.content))
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
        raise MoexError("MOEX ISS не ответил вовремя", code="moex_timeout")
    raise MoexError(f"Не удалось загрузить MOEX ISS ({'; '.join(errors)})", code="moex_network_error")


async def fetch_history_series(
    engine: str,
    market: str,
    security: str,
    *,
    value_column: str = "CLOSE",
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    end = to_date or datetime.now(timezone.utc).date()
    url = f"{MOEX_ISS_BASE}/history/engines/{engine}/markets/{market}/securities/{security}.json"
    merged: dict[date, Decimal] = {}
    start = 0

    while True:
        params = {
            "from": from_date.isoformat(),
            "till": end.isoformat(),
            "iss.meta": "off",
            "start": start,
        }
        payload = await _http_get_json(url, params)
        page_points, _, total = _parse_history_page(
            payload,
            value_column=value_column,
            from_date=from_date,
            to_date=end,
        )
        for observed, value in page_points:
            merged[observed] = value
        start += PAGE_SIZE
        if start >= total:
            break

    series = sorted(merged.items(), key=lambda item: item[0])
    if not series:
        raise MoexError("Не удалось получить ряд MOEX", code="moex_parse_error")
    logger.info(
        "moex_history_loaded",
        engine=engine,
        market=market,
        security=security,
        points=len(series),
        from_date=from_date.isoformat(),
        to_date=end.isoformat(),
    )
    return series


async def test_connection() -> dict:
    today = datetime.now(timezone.utc).date()
    from_date = date(today.year, 1, 1)
    series = await fetch_history_series(
        "stock",
        "index",
        "IMOEX",
        value_column="CLOSE",
        from_date=from_date,
        to_date=today,
    )
    observed, value = series[-1]
    return {
        "index_latest": {
            "security": "IMOEX",
            "date": observed.isoformat(),
            "value": str(value),
        },
    }
