from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.cbr.client import CbrError, fetch_key_rate_series, fetch_usd_rub_series
from app.integrations.cbr.mappings import CBR_MAPPINGS
from app.integrations.fred.transforms import compute_last_change
from app.models.indicators import Indicator, IndicatorValue
from app.models.providers import DataProvider

logger = structlog.get_logger()


async def sync_cbr(session: AsyncSession, provider: DataProvider) -> dict:
    total_records = 0
    synced_indicators: list[str] = []

    try:
        for mapping in CBR_MAPPINGS:
            indicator = await session.get(Indicator, mapping.indicator_id)
            if indicator is None:
                logger.warning("cbr_sync_skip_unknown_indicator", indicator_id=mapping.indicator_id)
                continue

            if mapping.series_type == "key_rate":
                series = await fetch_key_rate_series()
                external_id = "KeyRate"
            elif mapping.series_type == "usd_rub":
                series = await fetch_usd_rub_series(valuta_code=mapping.valuta_code or "R01235")
                external_id = mapping.valuta_code or "R01235"
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
                "cbr_sync_indicator",
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
            "message": f"ЦБ РФ: загружено {total_records} точек для {len(synced_indicators)} показателей",
            "records": total_records,
            "indicators": synced_indicators,
        }
    except CbrError as exc:
        await session.rollback()
        provider.last_sync_status = "error"
        await session.commit()
        logger.exception("cbr_sync_failed", error=exc.message)
        return {"ok": False, "error": exc.code, "message": exc.message}
    except Exception:
        await session.rollback()
        provider.last_sync_status = "error"
        await session.commit()
        logger.exception("cbr_sync_failed")
        return {"ok": False, "error": "sync_failed"}
