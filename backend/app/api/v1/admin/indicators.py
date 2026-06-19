from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_session
from app.data.catalog_templates import WAVES
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
    ImportTemplatesResult,
)

router = APIRouter(prefix="/admin/indicators", tags=["admin-indicators"])


@router.get("", response_model=list[AdminIndicatorItem])
async def get_admin_indicators(
    country: str | None = Query(default=None),
    source: str | None = Query(default=None),
    provider_id: str | None = Query(default=None),
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> list[AdminIndicatorItem]:
    rows = await list_admin_indicators(
        session,
        country=country,
        source=source,
        provider_id=provider_id,
    )
    return [AdminIndicatorItem(**row) for row in rows]


@router.post("", response_model=AdminIndicatorItem, status_code=status.HTTP_201_CREATED)
async def post_admin_indicator(
    body: AdminIndicatorCreate,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminIndicatorItem:
    try:
        row = await create_indicator(session, body)
    except ValueError as exc:
        if str(exc) == "indicator_exists":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Показатель уже существует") from exc
        raise
    return AdminIndicatorItem(
        id=row.id,
        name_ru=row.name_ru,
        country=row.country,
        category=row.category,
        frequency=row.frequency,
        source=row.source,
        external_id=row.external_id,
        unit=row.unit,
        has_data=False,
        enabled=True,
    )


@router.patch("/{indicator_id}", response_model=AdminIndicatorItem)
async def patch_admin_indicator(
    indicator_id: str,
    body: AdminIndicatorUpdate,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminIndicatorItem:
    row = await update_indicator(session, indicator_id, body)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Показатель не найден")
    rows = await list_admin_indicators(session)
    match = next((item for item in rows if item["id"] == indicator_id), None)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Показатель не найден")
    return AdminIndicatorItem(**match)


@router.get("/templates", response_model=list[CatalogTemplateItem])
async def get_catalog_templates(
    wave: str = Query(default="w1"),
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> list[CatalogTemplateItem]:
    if wave not in WAVES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неизвестная волна")
    rows = await list_catalog_templates(session, wave=wave)
    return [CatalogTemplateItem(**row) for row in rows]


@router.post("/import-templates", response_model=ImportTemplatesResult)
async def post_import_templates(
    wave: str = Query(default="w1"),
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> ImportTemplatesResult:
    if wave not in WAVES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неизвестная волна")
    imported, skipped = await import_templates(session, wave=wave)
    return ImportTemplatesResult(imported=imported, skipped=skipped)
