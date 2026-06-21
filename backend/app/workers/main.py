from __future__ import annotations

import asyncio
import signal

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

from app.config.settings import settings
from app.workers.jobs import run_daily_calendar_sync, run_daily_etl

structlog.configure(processors=[structlog.processors.JSONRenderer()])
logger = structlog.get_logger()


def _build_scheduler() -> AsyncIOScheduler:
    timezone = ZoneInfo(settings.etl_sync_timezone)
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
    return scheduler


async def main() -> None:
    scheduler = _build_scheduler()
    scheduler.start()
    logger.info(
        "worker_started",
        schedule=f"{settings.etl_sync_hour:02d}:{settings.etl_sync_minute:02d}",
        timezone=settings.etl_sync_timezone,
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _request_stop() -> None:
        stop.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _request_stop)

    await stop.wait()
    scheduler.shutdown(wait=False)
    logger.info("worker_stopped")


if __name__ == "__main__":
    asyncio.run(main())
