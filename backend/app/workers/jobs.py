from __future__ import annotations

import structlog

from app.db import SessionLocal
from app.etl.calendar.sync import run_calendar_sync_with_job
from app.etl.calendar.options import CalendarSyncOptions
from app.etl.sync import sync_all_enabled_providers

logger = structlog.get_logger()


async def run_daily_calendar_sync() -> None:
    logger.info("daily_calendar_sync_start")
    async with SessionLocal() as session:
        result = await run_calendar_sync_with_job(
            session,
            CalendarSyncOptions(trigger="scheduled"),
        )

    logger.info(
        "daily_calendar_sync_complete",
        ok=result.get("ok"),
        records=result.get("records"),
        enriched=result.get("enriched"),
    )


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
