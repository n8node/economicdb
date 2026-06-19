from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.options import SyncOptions
from app.etl.sync_runner import run_provider_indicator_sync
from app.integrations.world_bank.client import WorldBankError
from app.integrations.world_bank.indicator_fetch import fetch_world_bank_indicator
from app.models.providers import DataProvider


async def sync_world_bank(
    session: AsyncSession,
    provider: DataProvider,
    options: SyncOptions | None = None,
) -> dict:
    try:
        return await run_provider_indicator_sync(
            session,
            provider,
            options,
            fetch_one=fetch_world_bank_indicator,
            provider_label="World Bank",
        )
    except WorldBankError as exc:
        return {"ok": False, "error": exc.code, "message": exc.message}
