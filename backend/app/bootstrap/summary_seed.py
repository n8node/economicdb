import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.demo_summaries import DEMO_SUMMARIES
from app.models.summaries import WeeklySummary

logger = structlog.get_logger()


async def seed_demo_summaries(session: AsyncSession) -> None:
    count = await session.scalar(select(func.count()).select_from(WeeklySummary))
    if count and count > 0:
        logger.info("summary_seed_skipped", reason="weekly_summaries not empty")
        return

    for item in DEMO_SUMMARIES:
        session.add(WeeklySummary(**item))
    await session.commit()
    logger.info("summary_seed_complete", count=len(DEMO_SUMMARIES))
