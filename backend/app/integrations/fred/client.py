from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

import httpx
import structlog

logger = structlog.get_logger()

FRED_BASE_URL = "https://api.stlouisfed.org/fred"


class FredError(Exception):
    def __init__(self, message: str, *, code: str = "fred_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _parse_value(raw: str) -> Decimal | None:
    if raw in {".", "", "NaN"}:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


async def test_connection(api_key: str) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            f"{FRED_BASE_URL}/series",
            params={
                "series_id": "FEDFUNDS",
                "api_key": api_key,
                "file_type": "json",
            },
        )
        if response.status_code == 400:
            payload = response.json()
            error_msg = payload.get("error_message", "Неверный API key FRED")
            raise FredError(str(error_msg), code="invalid_api_key")
        response.raise_for_status()
        payload = response.json()
        series = (payload.get("seriess") or [{}])[0]
        obs = await fetch_observations(api_key, "FEDFUNDS", observation_start="2024-01-01", limit=1)
        latest = obs[-1] if obs else None
        return {
            "series_id": series.get("id", "FEDFUNDS"),
            "title": series.get("title"),
            "frequency": series.get("frequency"),
            "latest_observation": {"date": latest[0].isoformat(), "value": str(latest[1])} if latest else None,
        }


async def fetch_observations(
    api_key: str,
    series_id: str,
    *,
    observation_start: str = "2020-01-01",
    limit: int = 10000,
) -> list[tuple[date, Decimal]]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{FRED_BASE_URL}/series/observations",
            params={
                "series_id": series_id,
                "api_key": api_key,
                "file_type": "json",
                "observation_start": observation_start,
                "sort_order": "asc",
                "limit": limit,
            },
        )
        if response.status_code == 400:
            payload = response.json()
            error_msg = payload.get("error_message", f"Ошибка FRED для {series_id}")
            raise FredError(str(error_msg), code="fred_bad_request")
        response.raise_for_status()
        payload = response.json()

    points: list[tuple[date, Decimal]] = []
    for row in payload.get("observations", []):
        parsed = _parse_value(str(row.get("value", "")))
        if parsed is None:
            continue
        observed = date.fromisoformat(str(row["date"]))
        points.append((observed, parsed))
    return points
