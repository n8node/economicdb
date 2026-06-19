from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.helpers import indicator_matches_options, sources_for_provider
from app.etl.options import SyncOptions
from app.models.indicators import Indicator


async def load_provider_indicators(
    session: AsyncSession,
    provider_id: str,
    options: SyncOptions | None = None,
) -> list[Indicator]:
    sources = sources_for_provider(provider_id)
    if not sources:
        return []

    stmt = select(Indicator).where(Indicator.source.in_(sources)).order_by(Indicator.id)
    rows = list((await session.scalars(stmt)).all())
    return [row for row in rows if indicator_matches_options(row, options)]
