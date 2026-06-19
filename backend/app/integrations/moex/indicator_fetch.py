from __future__ import annotations

from datetime import date

from app.integrations.moex.client import MoexError, fetch_history_series
from app.models.indicators import Indicator


def parse_moex_external_id(external_id: str) -> tuple[str, str, str, str]:
    parts = external_id.strip("/").split("/")
    if len(parts) != 4:
        raise MoexError(f"Неверный MOEX external_id: {external_id}", code="moex_bad_external_id")
    engine, market, security, value_column = parts
    return engine, market, security, value_column


async def fetch_indicator_series(
    indicator: Indicator,
    *,
    from_date: date,
    to_date: date,
) -> tuple[list[tuple[date, object]], str]:
    external_id = (indicator.external_id or "").strip()
    if not external_id:
        raise MoexError(f"Нет external_id для {indicator.id}", code="moex_missing_external_id")

    engine, market, security, value_column = parse_moex_external_id(external_id)
    series = await fetch_history_series(
        engine,
        market,
        security,
        value_column=value_column,
        from_date=from_date,
        to_date=to_date,
    )
    if not series:
        raise MoexError(f"Пустой ряд MOEX {external_id}", code="moex_empty_series")
    return series, external_id
