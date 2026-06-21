from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_session
from app.etl.calendar.enricher import enrich_past_events
from app.etl.calendar.options import DEFAULT_CALENDAR_SOURCES, CalendarSyncOptions
from app.etl.calendar.sync import run_calendar_sync, run_calendar_sync_with_job
from app.etl.helpers import resolve_date_range
from app.etl.jobs_service import job_to_dict, list_etl_jobs
from app.etl.options import SyncOptions
from app.models.admin import AdminUser
from app.models.events import EconomicEvent
from app.schemas.calendar_admin import (
    CalendarEnrichRequest,
    CalendarSourceInfo,
    CalendarSourcesResponse,
    CalendarStatsResponse,
    CalendarSyncRequest,
    CalendarSyncResult,
)
from app.schemas.etl import EtlJobItem

router = APIRouter(prefix="/admin/calendar", tags=["admin-calendar"])

CALENDAR_SOURCE_META: list[CalendarSourceInfo] = [
    CalendarSourceInfo(
        id="fred",
        label="FRED (США)",
        description="ИПЦ, NFP, PCE, ВВП, промпроизводство — даты релизов через FRED API",
        requires_api_key=True,
        tier="B",
    ),
    CalendarSourceInfo(
        id="fomc",
        label="FOMC (Fed)",
        description="Заседания комитета по открытым рынкам — календарь federalreserve.gov",
        requires_api_key=False,
        tier="A",
    ),
    CalendarSourceInfo(
        id="cbr",
        label="Банк России",
        description="Заседания Совета директоров по ключевой ставке",
        requires_api_key=False,
        tier="A",
    ),
    CalendarSourceInfo(
        id="ecb",
        label="ECB",
        description="Заседания Governing Council по ставке ЕЦБ",
        requires_api_key=False,
        tier="A",
    ),
    CalendarSourceInfo(
        id="rosstat",
        label="Росстат",
        description="ИПЦ, промпроизводство, розница, PPI — ориентировочные даты публикаций",
        requires_api_key=False,
        tier="B",
    ),
]


def _options_from_request(body: CalendarSyncRequest, admin: AdminUser) -> CalendarSyncOptions:
    return CalendarSyncOptions(
        date_from=body.date_from,
        date_to=body.date_to,
        sources=body.sources,
        enrich=body.enrich,
        dry_run=body.dry_run,
        trigger="manual",
        admin_id=admin.id,
    )


@router.get("/sources", response_model=CalendarSourcesResponse)
async def calendar_sources(_: AdminUser = Depends(get_current_admin)) -> CalendarSourcesResponse:
    return CalendarSourcesResponse(sources=CALENDAR_SOURCE_META, default_sources=list(DEFAULT_CALENDAR_SOURCES))


@router.get("/defaults")
async def calendar_defaults(_: AdminUser = Depends(get_current_admin)) -> dict:
    from_date, to_date = resolve_date_range(None)
    return {
        "date_from": from_date.isoformat(),
        "date_to": to_date.isoformat(),
        "sources": list(DEFAULT_CALENDAR_SOURCES),
    }


@router.get("/stats", response_model=CalendarStatsResponse)
async def calendar_stats(
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> CalendarStatsResponse:
    now = datetime.now(timezone.utc)
    rows = list((await session.scalars(select(EconomicEvent))).all())
    by_source: dict[str, int] = {}
    by_country: dict[str, int] = {}
    upcoming = past = with_actual = with_forecast = 0

    for row in rows:
        by_source[row.source] = by_source.get(row.source, 0) + 1
        by_country[row.country] = by_country.get(row.country, 0) + 1
        if row.scheduled_at_msk > now:
            upcoming += 1
        else:
            past += 1
        if row.actual is not None:
            with_actual += 1
        if row.forecast is not None:
            with_forecast += 1

    return CalendarStatsResponse(
        total=len(rows),
        upcoming=upcoming,
        past=past,
        with_actual=with_actual,
        with_forecast=with_forecast,
        by_source=by_source,
        by_country=by_country,
    )


@router.post("/sync", response_model=CalendarSyncResult)
async def trigger_calendar_sync(
    body: CalendarSyncRequest,
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> CalendarSyncResult:
    opts = _options_from_request(body, admin)
    if opts.dry_run:
        result = await run_calendar_sync(session, opts)
        return CalendarSyncResult(**{k: result.get(k) for k in CalendarSyncResult.model_fields})

    result = await run_calendar_sync_with_job(session, opts)
    return CalendarSyncResult(**{k: result.get(k) for k in CalendarSyncResult.model_fields})


@router.post("/enrich", response_model=CalendarSyncResult)
async def trigger_calendar_enrich(
    body: CalendarEnrichRequest,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> CalendarSyncResult:
    enrich_result = await enrich_past_events(session, dry_run=body.dry_run)
    if not body.dry_run:
        await session.commit()
    return CalendarSyncResult(
        ok=True,
        message=f"Обогащено событий: {enrich_result['enriched']}",
        enriched=enrich_result["enriched"],
        records=enrich_result["enriched"],
        skipped=[{"reason": "no_indicator_data", "count": enrich_result["skipped"]}],
    )


@router.get("/jobs", response_model=list[EtlJobItem])
async def calendar_jobs(
    limit: int = Query(default=30, ge=1, le=100),
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> list[EtlJobItem]:
    jobs = await list_etl_jobs(session, provider_id="calendar", limit=limit)
    return [EtlJobItem(**job_to_dict(job)) for job in jobs]
