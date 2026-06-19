import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.fred.client import FredError, test_connection as fred_test_connection
from app.integrations.fred.sync import sync_fred
from app.models.providers import DataProvider
from app.services.credentials import get_api_key

logger = structlog.get_logger()

PROVIDERS_WITH_API_KEY = {"fred", "oecd"}


async def sync_provider(session: AsyncSession, provider_id: str) -> dict:
    provider = await session.get(DataProvider, provider_id)
    if provider is None:
        return {"ok": False, "error": "provider_not_found"}

    if not provider.enabled:
        return {"ok": False, "error": "provider_disabled"}

    if provider_id == "fred":
        return await sync_fred(session, provider)

    logger.info("etl_sync_unimplemented", provider_id=provider_id)
    return {
        "ok": False,
        "error": "provider_not_implemented",
        "message": "Синхронизация для этого провайдера ещё не реализована",
    }


async def test_provider_connection(
    session: AsyncSession,
    provider_id: str,
    *,
    api_key: str | None = None,
) -> dict:
    provider = await session.get(DataProvider, provider_id)
    if provider is None:
        return {"ok": False, "error": "provider_not_found"}

    key = (api_key or "").strip() or get_api_key(provider)
    if not key:
        return {"ok": False, "error": "missing_credentials", "message": "Укажите API key"}

    if provider_id == "fred":
        try:
            details = await fred_test_connection(key)
            return {
                "ok": True,
                "message": "Подключение к FRED успешно",
                "details": details,
            }
        except FredError as exc:
            return {"ok": False, "error": exc.code, "message": exc.message}

    return {
        "ok": False,
        "error": "provider_not_implemented",
        "message": "Проверка подключения для этого провайдера ещё не реализована",
    }


async def list_providers(session: AsyncSession) -> list[DataProvider]:
    result = await session.scalars(select(DataProvider).order_by(DataProvider.id))
    return list(result.all())
