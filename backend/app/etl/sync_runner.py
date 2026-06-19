from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.helpers import resolve_date_range
from app.etl.load_indicators import load_provider_indicators
from app.etl.options import SyncOptions
from app.etl.series_writer import write_indicator_series
from app.models.indicators import Indicator
from app.models.providers import DataProvider

logger = structlog.get_logger()

FetchFn = Callable[..., Awaitable[tuple[list[tuple[Any, Any]], str]]]


async def run_provider_indicator_sync(
    session: AsyncSession,
    provider: DataProvider,
    options: SyncOptions | None,
    *,
    fetch_one: FetchFn,
    fetch_kwargs: dict[str, Any] | None = None,
    provider_label: str,
) -> dict:
    from_date, to_date = resolve_date_range(options)
    dry_run = bool(options and options.dry_run)
    extra = fetch_kwargs or {}
    indicators = await load_provider_indicators(session, provider.id, options)

    total_records = 0
    synced_indicators: list[str] = []
    skipped: list[dict[str, str]] = []
    preview: list[dict] = []

    try:
        for indicator in indicators:
            try:
                series, external_id = await fetch_one(
                    indicator,
                    from_date=from_date,
                    to_date=to_date,
                    **extra,
                )
            except Exception as exc:
                message = getattr(exc, "message", str(exc))
                skipped.append({"indicator_id": indicator.id, "reason": message})
                logger.warning(
                    "provider_sync_skip_indicator",
                    provider_id=provider.id,
                    indicator_id=indicator.id,
                    error=message,
                )
                continue

            points = await write_indicator_series(
                session,
                indicator,
                series,
                external_id,
                dry_run=dry_run,
            )
            total_records += points
            synced_indicators.append(indicator.id)
            if dry_run:
                preview.append(
                    {
                        "indicator_id": indicator.id,
                        "points": points,
                        "first_date": series[0][0].isoformat(),
                        "last_date": series[-1][0].isoformat(),
                        "last_value": str(series[-1][1]),
                    }
                )

        if not dry_run:
            provider.last_sync_at = datetime.now(timezone.utc)
            provider.last_sync_status = "ok" if synced_indicators else "error"
        await session.commit()

        message = (
            f"{provider_label}: {'предпросмотр' if dry_run else 'загружено'} "
            f"{total_records} точек для {len(synced_indicators)} показателей"
        )
        if skipped:
            message += f", пропущено {len(skipped)}"

        return {
            "ok": bool(synced_indicators),
            "provider_id": provider.id,
            "message": message,
            "records": total_records,
            "indicators": synced_indicators,
            "skipped": skipped,
            "preview": preview if dry_run else None,
            "error": None if synced_indicators else "no_indicators_synced",
        }
    except Exception:
        await session.rollback()
        if not dry_run:
            provider.last_sync_status = "error"
            await session.commit()
        logger.exception("provider_sync_failed", provider_id=provider.id)
        return {"ok": False, "error": "sync_failed"}
