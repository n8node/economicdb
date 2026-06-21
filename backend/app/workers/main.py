from __future__ import annotations

import asyncio
import signal

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config.settings import settings
from app.core.timezones import get_tz
from app.workers.jobs import (
    bootstrap_weekly_digest_if_empty,
    run_daily_calendar_sync,
    run_daily_etl,
    run_weekly_digest,
)

structlog.configure(processors=[structlog.processors.JSONRenderer()])
logger = structlog.get_logger()


def _build_scheduler() -> AsyncIOScheduler:
    timezone = get_tz(settings.etl_sync_timezone)
    scheduler = AsyncIOScheduler(timezone=timezone)
    scheduler.add_job(
        run_daily_etl,
        CronTrigger(
            hour=settings.etl_sync_hour,
            minute=settings.etl_sync_minute,
            timezone=timezone,
        ),
        id="daily_etl",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_daily_calendar_sync,
        CronTrigger(
            hour=settings.calendar_sync_hour,
            minute=settings.calendar_sync_minute,
            timezone=timezone,
        ),
        id="daily_calendar",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_weekly_digest,
        CronTrigger(
            day_of_week=settings.digest_sync_day_of_week,
            hour=settings.digest_sync_hour,
            minute=settings.digest_sync_minute,
            timezone=timezone,
        ),
        id="weekly_digest",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler


async def main() -> None:
    scheduler = _build_scheduler()
    scheduler.start()
    logger.info(
        "worker_started",
        etl_schedule=f"{settings.etl_sync_hour:02d}:{settings.etl_sync_minute:02d}",
        digest_schedule=f"{settings.digest_sync_day_of_week} {settings.digest_sync_hour:02d}:{settings.digest_sync_minute:02d}",
        timezone=settings.etl_sync_timezone,
    )

    asyncio.create_task(_bootstrap_digest())

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _request_stop() -> None:
        stop.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _request_stop)

    await stop.wait()
    scheduler.shutdown(wait=False)
    logger.info("worker_stopped")


async def _bootstrap_digest() -> None:
    await asyncio.sleep(15)
    try:
        await bootstrap_weekly_digest_if_empty()
    except Exception:
        logger.exception("weekly_digest_bootstrap_failed")


if __name__ == "__main__":
    asyncio.run(main())
