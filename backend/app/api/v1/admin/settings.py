from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.openrouter import fetch_openrouter_models, test_openrouter_connection
from app.core.deps import get_current_admin, get_session
from app.models.admin import AdminUser
from app.schemas.admin_settings import (
    OpenRouterModelsRequest,
    OpenRouterModelsResponse,
    OpenRouterModelItem,
    OpenRouterSettingsResponse,
    OpenRouterSettingsUpdate,
    OpenRouterTestRequest,
    OpenRouterTestResult,
)
from app.services.settings_service import (
    DEFAULT_OPENROUTER_BASE_URL,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_META,
    OPENROUTER_MODEL_DIGEST,
    OPENROUTER_MODEL_FALLBACK,
    get_openrouter_api_key,
    get_openrouter_base_url,
    load_openrouter_settings,
    set_setting,
    set_setting_json,
)

router = APIRouter(prefix="/admin/settings", tags=["admin-settings"])
logger = structlog.get_logger()


def _model_label(model_id: str, name: str | None) -> str:
    if name and name != model_id:
        return f"{name} ({model_id})"
    return model_id


async def _resolve_openrouter_credentials(
    session: AsyncSession,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
) -> tuple[str, str]:
    resolved_key = await get_openrouter_api_key(session, api_key)
    if not resolved_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала сохраните API key OpenRouter",
        )
    resolved_base_url = await get_openrouter_base_url(session, base_url)
    return resolved_key, resolved_base_url


async def _write_openrouter_meta(
    session: AsyncSession,
    *,
    status_value: str,
    admin_id: int,
) -> None:
    await set_setting_json(
        session,
        OPENROUTER_META,
        {
            "last_test_at": datetime.now(timezone.utc).isoformat(),
            "last_test_status": status_value,
        },
        updated_by=admin_id,
    )


@router.get("/openrouter", response_model=OpenRouterSettingsResponse)
async def get_openrouter_settings(
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> OpenRouterSettingsResponse:
    data = await load_openrouter_settings(session)
    return OpenRouterSettingsResponse(**data)


@router.put("/openrouter", response_model=OpenRouterSettingsResponse)
async def update_openrouter_settings(
    body: OpenRouterSettingsUpdate,
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> OpenRouterSettingsResponse:
    if body.api_key is not None and body.api_key.strip():
        await set_setting(session, OPENROUTER_API_KEY, body.api_key.strip(), updated_by=admin.id)

    if body.base_url is not None:
        base_url = body.base_url.strip() or DEFAULT_OPENROUTER_BASE_URL
        await set_setting(session, OPENROUTER_BASE_URL, base_url, updated_by=admin.id)

    if body.model_digest is not None:
        model_digest = body.model_digest.strip()
        if model_digest:
            await set_setting(session, OPENROUTER_MODEL_DIGEST, model_digest, updated_by=admin.id)

    if body.model_fallback is not None:
        model_fallback = body.model_fallback.strip()
        if model_fallback:
            await set_setting(session, OPENROUTER_MODEL_FALLBACK, model_fallback, updated_by=admin.id)

    data = await load_openrouter_settings(session)
    return OpenRouterSettingsResponse(**data)


@router.post("/openrouter/test", response_model=OpenRouterTestResult)
async def test_openrouter_settings(
    body: OpenRouterTestRequest,
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> OpenRouterTestResult:
    try:
        api_key, base_url = await _resolve_openrouter_credentials(
            session,
            api_key=body.api_key,
            base_url=body.base_url,
        )
    except HTTPException as exc:
        return OpenRouterTestResult(ok=False, error="missing_api_key", message=str(exc.detail))

    try:
        result = await test_openrouter_connection(api_key, base_url)
    except Exception:
        logger.exception("openrouter_test_unhandled")
        await _write_openrouter_meta(session, status_value="error", admin_id=admin.id)
        return OpenRouterTestResult(
            ok=False,
            error="test_failed",
            message="Ошибка проверки подключения, подробности в логах backend",
        )

    await _write_openrouter_meta(
        session,
        status_value="ok" if result["ok"] else "error",
        admin_id=admin.id,
    )
    return OpenRouterTestResult(**result)


@router.get("/openrouter/models", response_model=OpenRouterModelsResponse)
async def list_openrouter_models(
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> OpenRouterModelsResponse:
    return await _load_openrouter_models(session)


@router.post("/openrouter/models", response_model=OpenRouterModelsResponse)
async def list_openrouter_models_with_credentials(
    body: OpenRouterModelsRequest,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> OpenRouterModelsResponse:
    return await _load_openrouter_models(session, api_key=body.api_key, base_url=body.base_url)


async def _load_openrouter_models(
    session: AsyncSession,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
) -> OpenRouterModelsResponse:
    try:
        resolved_key, resolved_base_url = await _resolve_openrouter_credentials(
            session,
            api_key=api_key,
            base_url=base_url,
        )
    except HTTPException as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc.detail)) from exc

    try:
        models = await fetch_openrouter_models(resolved_key, resolved_base_url)
    except Exception:
        logger.exception("openrouter_models_unhandled")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Не удалось загрузить список моделей OpenRouter",
        ) from None

    items = [
        OpenRouterModelItem(
            id=model["id"],
            name=model.get("name") or model["id"],
            label=_model_label(model["id"], model.get("name")),
        )
        for model in models
    ]
    return OpenRouterModelsResponse(items=items)
