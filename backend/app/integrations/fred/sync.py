from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.helpers import indicator_matches_options, resolve_date_range
from app.etl.options import SyncOptions
from app.etl.series_writer import write_indicator_series
from app.integrations.fred.client import FredError, fetch_observations
from app.integrations.fred.mappings import FRED_MAPPINGS
from app.integrations.fred.transforms import apply_transform
from app.models.indicators import Indicator
from app.models.providers import DataProvider
from app.services.credentials import get_api_key

logger = structlog.get_logger()


async def sync_fred(
    session: AsyncSession,
    provider: DataProvider,
    options: SyncOptions | None = None,
) -> dict:
    api_key = get_api_key(provider)
    if not api_key:
        return {"ok": False, "error": "missing_credentials"}

    from_date, to_date = resolve_date_range(options)
    dry_run = bool(options and options.dry_run)
    total_records = 0
    synced_indicators: list[str] = []
    preview: list[dict] = []

    try:
        for mapping in FRED_MAPPINGS:
            indicator = await session.get(Indicator, mapping.indicator_id)
            if not indicator_matches_options(indicator, options):
                continue

            raw = await fetch_observations(
                api_key,
                mapping.series_id,
                observation_start=from_date.isoformat(),
            )
            series = apply_transform(mapping.transform, raw)
            series = [(observed, value) for observed, value in series if observed <= to_date]
            if not series:
                logger.warning("fred_sync_empty_series", series_id=mapping.series_id)
                continue

            assert indicator is not None
            points = await write_indicator_series(
                session,
                indicator,
                series,
                mapping.series_id,
                dry_run=dry_run,
            )
            total_records += points
            synced_indicators.append(mapping.indicator_id)
            if dry_run:
                preview.append(
                    {
                        "indicator_id": mapping.indicator_id,
                        "points": points,
                        "first_date": series[0][0].isoformat(),
                        "last_date": series[-1][0].isoformat(),
                        "last_value": str(series[-1][1]),
                    }
                )

            logger.info(
                "fred_sync_indicator",
                indicator_id=mapping.indicator_id,
                series_id=mapping.series_id,
                points=len(series),
                dry_run=dry_run,
            )

        if not dry_run:
            provider.last_sync_at = datetime.now(timezone.utc)
            provider.last_sync_status = "ok"
        await session.commit()

        return {
            "ok": True,
            "provider_id": provider.id,
            "message": f"FRED: {'предпросмотр' if dry_run else 'загружено'} {total_records} точек для {len(synced_indicators)} показателей",
            "records": total_records,
            "indicators": synced_indicators,
            "preview": preview if dry_run else None,
        }
    except FredError as exc:
        await session.rollback()
        if not dry_run:
            provider.last_sync_status = "error"
            await session.commit()
        logger.exception("fred_sync_failed", error=exc.message)
        return {"ok": False, "error": exc.code, "message": exc.message}
    except Exception:
        await session.rollback()
        if not dry_run:
            provider.last_sync_status = "error"
            await session.commit()
        logger.exception("fred_sync_failed")
        return {"ok": False, "error": "sync_failed"}
