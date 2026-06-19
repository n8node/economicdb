from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import structlog
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.demo_indicators import DEMO_INDICATORS, generate_series
from app.models.indicators import Indicator, IndicatorValue

logger = structlog.get_logger()


async def seed_demo_indicators(session: AsyncSession) -> None:
    count = await session.scalar(select(func.count()).select_from(Indicator))
    if count and count > 0:
        logger.info("indicator_seed_skipped", reason="indicators not empty")
        return

    now = datetime.now(timezone.utc)
    for seed in DEMO_INDICATORS:
        series = generate_series(seed)
        last_date, last_val = series[-1]
        prev_val = series[-2][1] if len(series) > 1 else last_val
        change = last_val - prev_val if seed.unit in {"%", "п.п.", "index", "RUB", "USD"} else (
            (last_val - prev_val) / abs(prev_val) * 100 if prev_val else Decimal("0")
        )

        session.add(
            Indicator(
                id=seed.id,
                name_ru=seed.name_ru,
                country=seed.country,
                category=seed.category,
                frequency=seed.frequency,
                source=seed.source,
                external_id=seed.id,
                unit=seed.unit,
                last_value=last_val,
                last_change=Decimal(str(round(float(change), 2))),
                updated_at=now,
            )
        )
        for observed_at, value in series:
            session.add(
                IndicatorValue(
                    indicator_id=seed.id,
                    observed_at=observed_at,
                    value=value,
                )
            )

    await session.commit()
    logger.info("indicator_seed_complete", count=len(DEMO_INDICATORS))
