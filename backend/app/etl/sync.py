import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.providers import DataProvider

logger = structlog.get_logger()


async def sync_provider(session: AsyncSession, provider_id: str) -> dict:
    provider = await session.get(DataProvider, provider_id)
    if provider is None:
        return {"ok": False, "error": "provider_not_found"}

    if not provider.enabled:
        return {"ok": False, "error": "provider_disabled"}

    logger.info("etl_sync_stub", provider_id=provider_id)
    return {
        "ok": True,
        "provider_id": provider_id,
        "message": "ETL stub: провайдер зарегистрирован, загрузка данных будет в следующем этапе",
        "records": 0,
    }


async def list_providers(session: AsyncSession) -> list[DataProvider]:
    result = await session.scalars(select(DataProvider).order_by(DataProvider.id))
    return list(result.all())
