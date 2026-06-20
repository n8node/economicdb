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


async def resolve_futures_security(
    engine: str,
    market: str,
    asset_or_secid: str,
) -> str:
    """Map root asset codes (BR, GOLD) to the most liquid FORTS contract."""
    if len(asset_or_secid) > 4 or any(ch.isdigit() for ch in asset_or_secid[-2:]):
        return asset_or_secid

    url = f"{MOEX_ISS_BASE}/engines/{engine}/markets/{market}/securities.json"
    payload = await _http_get_json(url, {"iss.meta": "off"})
    table = payload.get("securities", {})
    columns = table.get("columns") if isinstance(table, dict) else None
    rows = table.get("data") if isinstance(table, dict) else None
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise MoexError("Не удалось прочитать список фьючерсов MOEX", code="moex_parse_error")

    col_index = {name: idx for idx, name in enumerate(columns)}
    asset_idx = col_index.get("ASSETCODE")
    secid_idx = col_index.get("SECID")
    oi_idx = col_index.get("OPENPOSITION")
    if asset_idx is None or secid_idx is None:
        raise MoexError("Некорректный формат списка фьючерсов MOEX", code="moex_parse_error")

    target = asset_or_secid.upper()
    candidates: list[tuple[int, str]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) <= max(asset_idx, secid_idx):
            continue
        asset_code = str(row[asset_idx] or "").upper()
        if asset_code != target:
            continue
        secid = str(row[secid_idx] or "").strip()
        if not secid:
            continue
        open_interest = 0
        if oi_idx is not None and len(row) > oi_idx and row[oi_idx] is not None:
            try:
                open_interest = int(row[oi_idx])
            except (TypeError, ValueError):
                open_interest = 0
        candidates.append((open_interest, secid))

    if not candidates:
        raise MoexError(f"Не найден фьючерс MOEX для {asset_or_secid}", code="moex_parse_error")
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


async def resolve_futures_candidates(
    engine: str,
    market: str,
    asset_or_secid: str,
    *,
    limit: int = 12,
) -> list[str]:
    primary = await resolve_futures_security(engine, market, asset_or_secid)
    url = f"{MOEX_ISS_BASE}/engines/{engine}/markets/{market}/securities.json"
    payload = await _http_get_json(url, {"iss.meta": "off"})
    table = payload.get("securities", {})
    columns = table.get("columns") if isinstance(table, dict) else None
    rows = table.get("data") if isinstance(table, dict) else None
    if not isinstance(columns, list) or not isinstance(rows, list):
        return [primary]

    col_index = {name: idx for idx, name in enumerate(columns)}
    asset_idx = col_index.get("ASSETCODE")
    secid_idx = col_index.get("SECID")
    oi_idx = col_index.get("OPENPOSITION")
    if asset_idx is None or secid_idx is None:
        return [primary]

    target = asset_or_secid.upper()
    candidates: list[tuple[int, str]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) <= max(asset_idx, secid_idx):
            continue
        if str(row[asset_idx] or "").upper() != target:
            continue
        secid = str(row[secid_idx] or "").strip()
        if not secid:
            continue
        open_interest = 0
        if oi_idx is not None and len(row) > oi_idx and row[oi_idx] is not None:
            try:
                open_interest = int(row[oi_idx])
            except (TypeError, ValueError):
                open_interest = 0
        candidates.append((open_interest, secid))

    ordered = [secid for _, secid in sorted(candidates, key=lambda item: item[0], reverse=True)]
    if primary not in ordered:
        ordered.insert(0, primary)
    return ordered[:limit] or [primary]


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
    securities = [security]
    if engine == "futures":
        securities = await resolve_futures_candidates(engine, market, security)

    merged: dict[date, Decimal] = {}
    last_error: MoexError | None = None
    for candidate in securities:
        try:
            series = await _fetch_history_for_security(
                engine,
                market,
                candidate,
                value_column=value_column,
                from_date=from_date,
                to_date=end,
            )
        except MoexError as exc:
            last_error = exc
            continue
        for observed, value in series:
            merged.setdefault(observed, value)

    series = sorted(merged.items(), key=lambda item: item[0])
    if series:
        logger.info(
            "moex_history_loaded",
            engine=engine,
            market=market,
            securities=securities,
            asset_or_secid=security,
            points=len(series),
            from_date=from_date.isoformat(),
            to_date=end.isoformat(),
        )
        return series

    if last_error is not None:
        raise last_error
    raise MoexError("Не удалось получить ряд MOEX", code="moex_parse_error")


async def _fetch_history_for_security(
    engine: str,
    market: str,
    resolved_security: str,
    *,
    value_column: str,
    from_date: date,
    to_date: date,
) -> list[tuple[date, Decimal]]:
    url = f"{MOEX_ISS_BASE}/history/engines/{engine}/markets/{market}/securities/{resolved_security}.json"
    merged: dict[date, Decimal] = {}
    start = 0

    while True:
        params = {
            "from": from_date.isoformat(),
            "till": to_date.isoformat(),
            "iss.meta": "off",
            "start": start,
        }
        payload = await _http_get_json(url, params)
        page_points, _, total = _parse_history_page(
            payload,
            value_column=value_column,
            from_date=from_date,
            to_date=to_date,
        )
        for observed, value in page_points:
            merged[observed] = value
        start += PAGE_SIZE
        if start >= total:
            break

    series = sorted(merged.items(), key=lambda item: item[0])
    if not series:
        raise MoexError("Не удалось получить ряд MOEX", code="moex_parse_error")
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
