from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_session
from app.etl.sync import list_providers, sync_provider
from app.models.admin import AdminUser
from app.schemas.providers import ProviderItem, SyncResult

router = APIRouter(prefix="/admin/providers", tags=["admin-providers"])


@router.get("", response_model=list[ProviderItem])
async def get_providers(
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> list[ProviderItem]:
    rows = await list_providers(session)
    return [
        ProviderItem(
            id=row.id,
            name_ru=row.name_ru,
            enabled=row.enabled,
            last_sync_at=row.last_sync_at.isoformat() if row.last_sync_at else None,
            last_sync_status=row.last_sync_status,
        )
        for row in rows
    ]


@router.post("/{provider_id}/sync", response_model=SyncResult)
async def trigger_sync(
    provider_id: str,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> SyncResult:
    result = await sync_provider(session, provider_id)
    if not result["ok"]:
        error = result.get("error", "sync_failed")
        if error == "provider_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Провайдер не найден")
        return SyncResult(ok=False, error=error)
    return SyncResult(
        ok=True,
        provider_id=result["provider_id"],
        message=result.get("message"),
        records=result.get("records"),
    )
