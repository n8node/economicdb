from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.catalog_templates import CatalogTemplate, templates_for_wave
from app.etl.helpers import sources_for_provider
from app.etl.sync_ready import is_sync_ready
from app.models.indicators import Indicator, IndicatorValue
from app.schemas.etl import AdminIndicatorCreate, AdminIndicatorUpdate


async def list_admin_indicators(
    session: AsyncSession,
    *,
    country: str | None = None,
    source: str | None = None,
    provider_id: str | None = None,
) -> list[dict]:
    stmt = select(Indicator).order_by(Indicator.country, Indicator.category, Indicator.id)
    if country:
        stmt = stmt.where(Indicator.country == country)
    if source:
        stmt = stmt.where(Indicator.source == source)
    elif provider_id:
        sources = sources_for_provider(provider_id)
        if sources:
            stmt = stmt.where(Indicator.source.in_(sources))

    indicators = list((await session.scalars(stmt)).all())
    if not indicators:
        return []

    ids = [item.id for item in indicators]
    counts_stmt = (
        select(IndicatorValue.indicator_id, func.count())
        .where(IndicatorValue.indicator_id.in_(ids))
        .group_by(IndicatorValue.indicator_id)
    )
    counts = {row[0]: row[1] for row in (await session.execute(counts_stmt)).all()}

    return [
        {
            "id": item.id,
            "name_ru": item.name_ru,
            "country": item.country,
            "category": item.category,
            "frequency": item.frequency,
            "source": item.source,
            "external_id": item.external_id,
            "unit": item.unit,
            "last_value": str(item.last_value) if item.last_value is not None else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "has_data": counts.get(item.id, 0) > 0,
            "data_points": counts.get(item.id, 0),
            "sync_ready": is_sync_ready(item),
            "enabled": item.enabled,
        }
        for item in indicators
    ]


async def create_indicator(session: AsyncSession, payload: AdminIndicatorCreate) -> Indicator:
    existing = await session.get(Indicator, payload.id)
    if existing is not None:
        raise ValueError("indicator_exists")
    row = Indicator(
        id=payload.id,
        name_ru=payload.name_ru,
        country=payload.country,
        category=payload.category,
        frequency=payload.frequency,
        source=payload.source,
        external_id=payload.external_id,
        unit=payload.unit,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def update_indicator(
    session: AsyncSession,
    indicator_id: str,
    payload: AdminIndicatorUpdate,
) -> Indicator | None:
    row = await session.get(Indicator, indicator_id)
    if row is None:
        return None
    if payload.name_ru is not None:
        row.name_ru = payload.name_ru
    if payload.category is not None:
        row.category = payload.category
    if payload.external_id is not None:
        row.external_id = payload.external_id
    if payload.unit is not None:
        row.unit = payload.unit
    if payload.enabled is not None:
        row.enabled = payload.enabled
    await session.commit()
    await session.refresh(row)
    return row


async def import_templates(
    session: AsyncSession,
    *,
    wave: str,
) -> tuple[list[str], list[str]]:
    imported: list[str] = []
    skipped: list[str] = []
    for template in templates_for_wave(wave):
        existing = await session.get(Indicator, template.id)
        if existing is not None:
            skipped.append(template.id)
            continue
        session.add(_template_to_indicator(template))
        imported.append(template.id)
    await session.commit()
    return imported, skipped


def _template_to_indicator(template: CatalogTemplate) -> Indicator:
    return Indicator(
        id=template.id,
        name_ru=template.name_ru,
        country=template.country,
        category=template.category,
        frequency=template.frequency,
        source=template.source,
        external_id=template.external_id,
        unit=template.unit,
    )


async def list_catalog_templates(session: AsyncSession, *, wave: str = "w1") -> list[dict]:
    existing_ids = set(await session.scalars(select(Indicator.id)))
    return [
        {
            "id": item.id,
            "name_ru": item.name_ru,
            "country": item.country,
            "category": item.category,
            "frequency": item.frequency,
            "source": item.source,
            "external_id": item.external_id,
            "unit": item.unit,
            "wave": item.wave,
            "in_catalog": item.id in existing_ids,
        }
        for item in templates_for_wave(wave)
    ]
