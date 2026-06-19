import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.demo_events import DEMO_EVENTS
from app.models.events import EconomicEvent

logger = structlog.get_logger()


async def seed_demo_events(session: AsyncSession) -> None:
    count = await session.scalar(select(func.count()).select_from(EconomicEvent))
    if count and count > 0:
        logger.info("event_seed_skipped", reason="economic_events not empty")
        return

    for seed in DEMO_EVENTS:
        surprise = seed.actual - seed.forecast if seed.actual is not None and seed.forecast is not None else None
        session.add(
            EconomicEvent(
                id=seed.id,
                title_ru=seed.title_ru,
                country=seed.country,
                category=seed.category,
                importance=seed.importance,
                scheduled_at_msk=seed.scheduled_at_msk,
                actual=seed.actual,
                forecast=seed.forecast,
                previous=seed.previous,
                surprise=surprise,
                linked_indicator_id=seed.linked_indicator_id,
                source=seed.source,
                unit=seed.unit,
            )
        )
    await session.commit()
    logger.info("event_seed_complete", count=len(DEMO_EVENTS))
