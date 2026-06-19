from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.helpers import indicator_matches_options, resolve_date_range
from app.etl.options import SyncOptions
from app.etl.series_writer import write_indicator_series
from app.integrations.imf.client import ImfError, fetch_gdp_yoy_series
from app.integrations.imf.mappings import IMF_MAPPINGS
from app.models.indicators import Indicator
from app.models.providers import DataProvider

logger = structlog.get_logger()


async def sync_imf(
    session: AsyncSession,
    provider: DataProvider,
    options: SyncOptions | None = None,
) -> dict:
    from_date, to_date = resolve_date_range(options)
    dry_run = bool(options and options.dry_run)
    total_records = 0
    synced_indicators: list[str] = []

    try:
        for mapping in IMF_MAPPINGS:
            indicator = await session.get(Indicator, mapping.indicator_id)
            if not indicator_matches_options(indicator, options):
                continue

            if mapping.series_type == "gdp_yoy":
                series = await fetch_gdp_yoy_series(
                    mapping.indicator_code,
                    mapping.country_code,
                    from_date=from_date,
                    to_date=to_date,
                )
            else:
                continue

            assert indicator is not None
            external_id = f"{mapping.indicator_code}/{mapping.country_code}"
            total_records += await write_indicator_series(
                session,
                indicator,
                series,
                external_id,
                dry_run=dry_run,
            )
            synced_indicators.append(mapping.indicator_id)

        if not dry_run:
            provider.last_sync_at = datetime.now(timezone.utc)
            provider.last_sync_status = "ok"
        await session.commit()

        return {
            "ok": True,
            "provider_id": provider.id,
            "message": f"IMF: {'предпросмотр' if dry_run else 'загружено'} {total_records} точек для {len(synced_indicators)} показателей",
            "records": total_records,
            "indicators": synced_indicators,
        }
    except ImfError as exc:
        await session.rollback()
        if not dry_run:
            provider.last_sync_status = "error"
            await session.commit()
        logger.exception("imf_sync_failed", error=exc.message)
        return {"ok": False, "error": exc.code, "message": exc.message}
    except Exception:
        await session.rollback()
        if not dry_run:
            provider.last_sync_status = "error"
            await session.commit()
        logger.exception("imf_sync_failed")
        return {"ok": False, "error": "sync_failed"}
