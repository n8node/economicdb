from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.options import SyncOptions
from app.etl.sync_runner import run_provider_indicator_sync
from app.integrations.cbr.client import CbrError
from app.integrations.cbr.indicator_fetch import fetch_indicator_series
from app.models.providers import DataProvider


async def sync_cbr(
    session: AsyncSession,
    provider: DataProvider,
    options: SyncOptions | None = None,
) -> dict:
    try:
        return await run_provider_indicator_sync(
            session,
            provider,
            options,
            fetch_one=fetch_indicator_series,
            provider_label="ЦБ РФ",
        )
    except CbrError as exc:
        return {"ok": False, "error": exc.code, "message": exc.message}
