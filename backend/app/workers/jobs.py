from __future__ import annotations

import structlog

from app.db import SessionLocal
from app.etl.calendar.options import CalendarSyncOptions
from app.etl.calendar.sync import run_calendar_sync_with_job
from app.etl.sync import sync_all_enabled_providers
from app.services.digest import generate_and_store_weekly_digest, has_published_summaries

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


async def run_weekly_digest(*, force: bool = False) -> None:
    logger.info("weekly_digest_start", force=force)
    async with SessionLocal() as session:
        result = await generate_and_store_weekly_digest(session, force=force)

    logger.info("weekly_digest_complete", **{k: v for k, v in result.items() if k != "message"})


async def bootstrap_weekly_digest_if_empty() -> None:
    async with SessionLocal() as session:
        if await has_published_summaries(session):
            return
    logger.info("weekly_digest_bootstrap_start")
    await run_weekly_digest(force=True)
