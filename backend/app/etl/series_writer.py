from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.fred.transforms import compute_last_change
from app.models.indicators import Indicator, IndicatorValue


async def write_indicator_series(
    session: AsyncSession,
    indicator: Indicator,
    series: list[tuple[date, Decimal]],
    external_id: str,
    *,
    dry_run: bool = False,
) -> int:
    if not series:
        return 0
    if dry_run:
        return len(series)

    for observed_at, value in series:
        stmt = (
            insert(IndicatorValue)
            .values(
                indicator_id=indicator.id,
                observed_at=observed_at,
                value=value,
            )
            .on_conflict_do_update(
                index_elements=["indicator_id", "observed_at"],
                set_={"value": value},
            )
        )
        await session.execute(stmt)

    last_date, last_val = series[-1]
    indicator.external_id = external_id
    indicator.last_value = last_val
    indicator.last_change = compute_last_change(series, indicator.unit)
    indicator.updated_at = datetime.now(timezone.utc)
    return len(series)
