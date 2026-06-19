from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import structlog
from sqlalchemy import delete, select, update

from app.bootstrap.indicator_seed import REAL_INDICATOR_IDS, seed_real_indicators
from app.db import SessionLocal
from app.etl.sync import sync_all_enabled_providers
from app.models.events import EconomicEvent
from app.models.indicators import Indicator, IndicatorValue
from app.models.summaries import WeeklySummary

logger = structlog.get_logger()


async def cleanup_demo_data() -> dict:
    async with SessionLocal() as session:
        await seed_real_indicators(session)

        await session.execute(delete(WeeklySummary))
        await session.execute(delete(EconomicEvent))
        await session.execute(delete(IndicatorValue))
        await session.execute(delete(Indicator).where(Indicator.id.not_in(REAL_INDICATOR_IDS)))
        await session.execute(
            update(Indicator)
            .where(Indicator.id.in_(REAL_INDICATOR_IDS))
            .values(
                last_value=None,
                last_change=None,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

        sync_result = await sync_all_enabled_providers(session)
        return {
            "ok": True,
            "kept_indicators": sorted(REAL_INDICATOR_IDS),
            "sync": sync_result,
        }


async def main() -> None:
    result = await cleanup_demo_data()
    logger.info("cleanup_demo_data_complete", **result)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
