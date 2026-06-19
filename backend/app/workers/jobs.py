from __future__ import annotations

import structlog

from app.db import SessionLocal
from app.etl.sync import sync_all_enabled_providers

logger = structlog.get_logger()


async def run_daily_etl() -> None:
    logger.info("daily_etl_start")
    async with SessionLocal() as session:
        result = await sync_all_enabled_providers(session)

    logger.info(
        "daily_etl_complete",
        ok=result.get("ok"),
        total_records=result.get("total_records"),
        providers=len(result.get("providers") or []),
    )
