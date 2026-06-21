from __future__ import annotations

from datetime import date, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.calendar.enricher import enrich_past_events
from app.etl.calendar.options import CALENDAR_PROVIDER_ID, CalendarSyncOptions
from app.etl.calendar.writer import upsert_events
from app.etl.helpers import resolve_date_range
from app.etl.jobs_service import create_etl_job, finish_etl_job
from app.etl.options import SyncOptions
from app.integrations.cbr.calendar_fetch import fetch_cbr_calendar_events
from app.integrations.ecb_eurostat.calendar_fetch import fetch_ecb_calendar_events
from app.integrations.fred.calendar_fetch import fetch_fred_calendar_events
from app.integrations.fred.fomc_calendar_fetch import fetch_fomc_calendar_events
from app.integrations.rosstat.calendar_fetch import fetch_rosstat_calendar_events
from app.models.etl_jobs import EtlJob
from app.models.providers import DataProvider
from app.services.credentials import get_api_key

logger = structlog.get_logger()

DEFAULT_LOOKBACK_DAYS = 90
DEFAULT_LOOKAHEAD_DAYS = 120


def _resolve_calendar_range(options: CalendarSyncOptions | None) -> tuple[date, date]:
    if options and (options.date_from or options.date_to):
        from_date, to_date = resolve_date_range(
            SyncOptions(date_from=options.date_from, date_to=options.date_to)
        )
        return from_date, to_date
    today = date.today()
    return today - timedelta(days=DEFAULT_LOOKBACK_DAYS), today + timedelta(days=DEFAULT_LOOKAHEAD_DAYS)


async def run_calendar_sync(
    session: AsyncSession,
    options: CalendarSyncOptions | None = None,
) -> dict:
    opts = options or CalendarSyncOptions()
    date_from, date_to = _resolve_calendar_range(opts)
    sources = opts.sources or list(CalendarSyncOptions().sources)
    dry_run = opts.dry_run

    all_drafts = []
    skipped: list[dict] = []
    source_stats: dict[str, int] = {}

    if "fred" in sources:
        provider = await session.get(DataProvider, "fred")
        api_key = get_api_key(provider) if provider else None
        if not api_key:
            skipped.append({"source": "fred", "reason": "missing_credentials"})
        else:
            drafts, fred_skipped = await fetch_fred_calendar_events(
                api_key,
                date_from=date_from,
                date_to=date_to,
            )
            all_drafts.extend(drafts)
            skipped.extend(fred_skipped)
            source_stats["fred"] = len(drafts)

    if "cbr" in sources:
        drafts = await fetch_cbr_calendar_events(date_from=date_from, date_to=date_to)
        all_drafts.extend(drafts)
        source_stats["cbr"] = len(drafts)

    if "ecb" in sources:
        drafts = await fetch_ecb_calendar_events(date_from=date_from, date_to=date_to)
        all_drafts.extend(drafts)
        source_stats["ecb"] = len(drafts)

    if "fomc" in sources:
        drafts = await fetch_fomc_calendar_events(date_from=date_from, date_to=date_to)
        all_drafts.extend(drafts)
        source_stats["fomc"] = len(drafts)

    if "rosstat" in sources:
        drafts = await fetch_rosstat_calendar_events(date_from=date_from, date_to=date_to)
        all_drafts.extend(drafts)
        source_stats["rosstat"] = len(drafts)

    unique: dict[str, object] = {}
    for draft in all_drafts:
        unique[draft.id] = draft
    deduped = list(unique.values())

    records, synced_ids = await upsert_events(session, deduped, dry_run=dry_run)

    enrich_result = {"enriched": 0, "skipped": 0}
    if opts.enrich and not dry_run:
        enrich_result = await enrich_past_events(session, dry_run=dry_run)

    message = (
        f"Календарь: {records} событий ({date_from.isoformat()} — {date_to.isoformat()}). "
        f"Обогащено: {enrich_result.get('enriched', 0)}."
    )

    logger.info(
        "calendar_sync_complete",
        records=records,
        sources=source_stats,
        enriched=enrich_result.get("enriched"),
        dry_run=dry_run,
    )

    return {
        "ok": True,
        "provider_id": CALENDAR_PROVIDER_ID,
        "records": records,
        "message": message,
        "indicators": synced_ids[:100],
        "sources": source_stats,
        "skipped": skipped,
        "enriched": enrich_result.get("enriched", 0),
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    }


async def run_calendar_sync_with_job(
    session: AsyncSession,
    options: CalendarSyncOptions | None = None,
) -> dict:
    opts = options or CalendarSyncOptions()
    if opts.dry_run:
        return await run_calendar_sync(session, opts)

    date_from, date_to = _resolve_calendar_range(opts)
    job = await create_etl_job(
        session,
        CALENDAR_PROVIDER_ID,
        SyncOptions(
            date_from=date_from,
            date_to=date_to,
            indicator_ids=opts.sources,
            dry_run=False,
            trigger=opts.trigger,
            admin_id=opts.admin_id,
        ),
    )
    await session.commit()
    job_id = job.id
    try:
        result = await run_calendar_sync(session, opts)
        job = await session.get(EtlJob, job_id)
        if job is not None:
            await finish_etl_job(session, job, result)
        await session.commit()
        return {**result, "job_id": job_id}
    except Exception as exc:
        await session.rollback()
        job = await session.get(EtlJob, job_id)
        if job is not None:
            await finish_etl_job(
                session,
                job,
                {"ok": False, "records": 0, "message": str(exc), "error": "sync_failed"},
            )
            await session.commit()
        raise
