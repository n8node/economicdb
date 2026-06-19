from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.options import SyncOptions
from app.etl.sync_runner import run_provider_indicator_sync
from app.integrations.fred.client import FredError
from app.integrations.fred.indicator_fetch import fetch_indicator_series
from app.models.providers import DataProvider
from app.services.credentials import get_api_key


async def sync_fred(
    session: AsyncSession,
    provider: DataProvider,
    options: SyncOptions | None = None,
) -> dict:
    api_key = get_api_key(provider)
    if not api_key:
        return {"ok": False, "error": "missing_credentials"}

    async def fetch_one(indicator, *, from_date, to_date, **_kwargs):
        return await fetch_indicator_series(
            indicator,
            api_key,
            from_date=from_date,
            to_date=to_date,
        )

    try:
        return await run_provider_indicator_sync(
            session,
            provider,
            options,
            fetch_one=fetch_one,
            provider_label="FRED",
        )
    except FredError as exc:
        return {"ok": False, "error": exc.code, "message": exc.message}
