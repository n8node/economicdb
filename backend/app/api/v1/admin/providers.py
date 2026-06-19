import structlog
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_session
from app.etl.sync import PROVIDERS_WITH_API_KEY, list_providers, sync_provider, test_provider_connection
from app.models.admin import AdminUser
from app.models.providers import DataProvider
from app.schemas.providers import (
    ProviderCredentialsUpdate,
    ProviderItem,
    ProviderUpdate,
    SyncResult,
    TestConnectionRequest,
    TestConnectionResult,
)
from app.services.credentials import has_stored_credentials, save_api_key

router = APIRouter(prefix="/admin/providers", tags=["admin-providers"])
logger = structlog.get_logger()


def _provider_item(row: DataProvider) -> ProviderItem:
    return ProviderItem(
        id=row.id,
        name_ru=row.name_ru,
        enabled=row.enabled,
        base_url=row.base_url,
        has_credentials=has_stored_credentials(row),
        supports_credentials=row.id in PROVIDERS_WITH_API_KEY,
        last_test_at=row.last_test_at.isoformat() if row.last_test_at else None,
        last_test_status=row.last_test_status,
        last_sync_at=row.last_sync_at.isoformat() if row.last_sync_at else None,
        last_sync_status=row.last_sync_status,
    )


@router.get("", response_model=list[ProviderItem])
async def get_providers(
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> list[ProviderItem]:
    rows = await list_providers(session)
    return [_provider_item(row) for row in rows]


@router.patch("/{provider_id}", response_model=ProviderItem)
async def update_provider(
    provider_id: str,
    body: ProviderUpdate,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> ProviderItem:
    provider = await session.get(DataProvider, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Провайдер не найден")

    if body.enabled and provider_id in PROVIDERS_WITH_API_KEY and not has_stored_credentials(provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала сохраните API key",
        )

    provider.enabled = body.enabled
    await session.commit()
    await session.refresh(provider)
    return _provider_item(provider)


@router.put("/{provider_id}/credentials", response_model=ProviderItem)
async def set_provider_credentials(
    provider_id: str,
    body: ProviderCredentialsUpdate,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> ProviderItem:
    if provider_id not in PROVIDERS_WITH_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Этот провайдер не использует API key",
        )

    provider = await session.get(DataProvider, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Провайдер не найден")

    await save_api_key(session, provider, body.api_key)
    await session.refresh(provider)
    return _provider_item(provider)


@router.post("/{provider_id}/test", response_model=TestConnectionResult)
async def test_provider(
    provider_id: str,
    body: TestConnectionRequest,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> TestConnectionResult:
    provider = await session.get(DataProvider, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Провайдер не найден")

    try:
        result = await test_provider_connection(session, provider_id, api_key=body.api_key)
    except Exception:
        logger.exception("provider_test_unhandled", provider_id=provider_id)
        provider.last_test_at = datetime.now(timezone.utc)
        provider.last_test_status = "error"
        await session.commit()
        return TestConnectionResult(
            ok=False,
            error="test_failed",
            message="Ошибка проверки подключения, подробности в логах backend",
        )
    if not result["ok"]:
        error = result.get("error", "test_failed")
        if error == "provider_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Провайдер не найден")
        provider.last_test_at = datetime.now(timezone.utc)
        provider.last_test_status = "error"
        await session.commit()
        return TestConnectionResult(
            ok=False,
            error=error,
            message=result.get("message"),
        )
    provider.last_test_at = datetime.now(timezone.utc)
    provider.last_test_status = "ok"
    await session.commit()
    return TestConnectionResult(
        ok=True,
        message=result.get("message"),
        details=result.get("details"),
    )


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
        return SyncResult(
            ok=False,
            error=error,
            message=result.get("message"),
        )
    return SyncResult(
        ok=True,
        provider_id=result["provider_id"],
        message=result.get("message"),
        records=result.get("records"),
    )
