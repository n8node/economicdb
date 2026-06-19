from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.fred.transforms import compute_last_change
from app.integrations.rosstat.client import RosstatError, fetch_cpi_yoy_series
from app.integrations.rosstat.mappings import ROSSTAT_MAPPINGS
from app.models.indicators import Indicator, IndicatorValue
from app.models.providers import DataProvider

logger = structlog.get_logger()


async def sync_rosstat(session: AsyncSession, provider: DataProvider) -> dict:
    total_records = 0
    synced_indicators: list[str] = []

    try:
        for mapping in ROSSTAT_MAPPINGS:
            indicator = await session.get(Indicator, mapping.indicator_id)
            if indicator is None:
                logger.warning("rosstat_sync_skip_unknown_indicator", indicator_id=mapping.indicator_id)
                continue

            if mapping.series_type == "cpi_yoy":
                series = await fetch_cpi_yoy_series()
                external_id = "CPI_YOY"
            else:
                continue

            for observed_at, value in series:
                stmt = (
                    insert(IndicatorValue)
                    .values(
                        indicator_id=mapping.indicator_id,
                        observed_at=observed_at,
                        value=value,
                    )
                    .on_conflict_do_update(
                        index_elements=["indicator_id", "observed_at"],
                        set_={"value": value},
                    )
                )
                await session.execute(stmt)
                total_records += 1

            last_date, last_val = series[-1]
            indicator.external_id = external_id
            indicator.last_value = last_val
            indicator.last_change = compute_last_change(series, indicator.unit)
            indicator.updated_at = datetime.now(timezone.utc)
            synced_indicators.append(mapping.indicator_id)

            logger.info(
                "rosstat_sync_indicator",
                indicator_id=mapping.indicator_id,
                points=len(series),
                last_date=last_date.isoformat(),
                last_value=str(last_val),
            )

        provider.last_sync_at = datetime.now(timezone.utc)
        provider.last_sync_status = "ok"
        await session.commit()

        return {
            "ok": True,
            "provider_id": provider.id,
            "message": f"Росстат: загружено {total_records} точек для {len(synced_indicators)} показателей",
            "records": total_records,
            "indicators": synced_indicators,
        }
    except RosstatError as exc:
        await session.rollback()
        provider.last_sync_status = "error"
        await session.commit()
        logger.exception("rosstat_sync_failed", error=exc.message)
        return {"ok": False, "error": exc.code, "message": exc.message}
    except Exception:
        await session.rollback()
        provider.last_sync_status = "error"
        await session.commit()
        logger.exception("rosstat_sync_failed")
        return {"ok": False, "error": "sync_failed"}
