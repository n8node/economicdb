from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_session
from app.data.catalog_templates import WAVES
from app.etl.helpers import resolve_date_range
from app.etl.jobs_service import job_to_dict, list_etl_jobs
from app.etl.options import SyncOptions
from app.etl.sync import run_sync_with_job
from app.models.admin import AdminUser
from app.repositories.admin_indicators import (
    create_indicator,
    import_templates,
    list_admin_indicators,
    list_catalog_templates,
    update_indicator,
)
from app.schemas.etl import (
    AdminIndicatorCreate,
    AdminIndicatorItem,
    AdminIndicatorUpdate,
    CatalogTemplateItem,
    EtlJobItem,
    EtlPreviewRequest,
    EtlSyncRequest,
    EtlSyncResult,
    ImportTemplatesResult,
)

router = APIRouter(prefix="/admin/etl", tags=["admin-etl"])


def _options_from_request(body: EtlSyncRequest, admin: AdminUser) -> SyncOptions:
    return SyncOptions(
        date_from=body.date_from,
        date_to=body.date_to,
        indicator_ids=body.indicator_ids,
        country=body.country,
        dry_run=body.dry_run,
        trigger="manual",
        admin_id=admin.id,
    )


@router.post("/sync", response_model=EtlSyncResult)
async def trigger_etl_sync(
    body: EtlSyncRequest,
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> EtlSyncResult:
    result = await run_sync_with_job(session, body.provider_id, _options_from_request(body, admin))
    if not result["ok"]:
        error = result.get("error", "sync_failed")
        if error == "provider_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Провайдер не найден")
        return EtlSyncResult(
            ok=False,
            provider_id=body.provider_id,
            job_id=result.get("job_id"),
            error=error,
            message=result.get("message"),
        )
    return EtlSyncResult(
        ok=True,
        provider_id=result.get("provider_id"),
        job_id=result.get("job_id"),
        message=result.get("message"),
        records=result.get("records"),
        indicators=result.get("indicators"),
        preview=result.get("preview"),
    )


@router.post("/preview", response_model=EtlSyncResult)
async def preview_etl_sync(
    body: EtlPreviewRequest,
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> EtlSyncResult:
    preview_body = body.model_copy(update={"dry_run": True})
    return await trigger_etl_sync(preview_body, admin, session)


@router.get("/jobs", response_model=list[EtlJobItem])
async def get_etl_jobs(
    provider_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> list[EtlJobItem]:
    jobs = await list_etl_jobs(session, provider_id=provider_id, limit=limit)
    return [EtlJobItem(**job_to_dict(job)) for job in jobs]


@router.get("/defaults")
async def get_etl_defaults(
    _: AdminUser = Depends(get_current_admin),
) -> dict:
    from_date, to_date = resolve_date_range(None)
    return {
        "date_from": from_date.isoformat(),
        "date_to": to_date.isoformat(),
        "waves": list(WAVES),
    }
