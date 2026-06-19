import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.cbr.client import CbrError, test_connection as cbr_test_connection
from app.integrations.cbr.sync import sync_cbr
from app.integrations.fred.client import FredError, test_connection as fred_test_connection
from app.integrations.fred.sync import sync_fred
from app.integrations.oecd.client import OecdError, test_connection as oecd_test_connection
from app.integrations.oecd.sync import sync_oecd
from app.integrations.rosstat.client import RosstatError, test_connection as rosstat_test_connection
from app.integrations.rosstat.sync import sync_rosstat
from app.models.providers import DataProvider
from app.services.credentials import get_api_key

logger = structlog.get_logger()

PROVIDERS_WITH_API_KEY = {"fred"}


async def sync_provider(session: AsyncSession, provider_id: str) -> dict:
    provider = await session.get(DataProvider, provider_id)
    if provider is None:
        return {"ok": False, "error": "provider_not_found"}

    if not provider.enabled:
        return {"ok": False, "error": "provider_disabled"}

    if provider_id == "fred":
        return await sync_fred(session, provider)

    if provider_id == "cbr":
        return await sync_cbr(session, provider)

    if provider_id == "rosstat":
        return await sync_rosstat(session, provider)

    if provider_id == "oecd":
        return await sync_oecd(session, provider)

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

    if provider_id == "cbr":
        try:
            details = await cbr_test_connection()
            return {
                "ok": True,
                "message": "Подключение к ЦБ РФ успешно",
                "details": details,
            }
        except CbrError as exc:
            return {"ok": False, "error": exc.code, "message": exc.message}
        except Exception:
            logger.exception("cbr_test_connection_failed")
            return {
                "ok": False,
                "error": "cbr_test_failed",
                "message": "Ошибка проверки ЦБ РФ, подробности в логах backend",
            }

    if provider_id == "rosstat":
        try:
            details = await rosstat_test_connection()
            return {
                "ok": True,
                "message": "Подключение к Росстату успешно",
                "details": details,
            }
        except RosstatError as exc:
            return {"ok": False, "error": exc.code, "message": exc.message}
        except Exception:
            logger.exception("rosstat_test_connection_failed")
            return {
                "ok": False,
                "error": "rosstat_test_failed",
                "message": "Ошибка проверки Росстата, подробности в логах backend",
            }

    if provider_id == "oecd":
        try:
            details = await oecd_test_connection()
            return {
                "ok": True,
                "message": "Подключение к OECD SDMX успешно",
                "details": details,
            }
        except OecdError as exc:
            return {"ok": False, "error": exc.code, "message": exc.message}
        except Exception:
            logger.exception("oecd_test_connection_failed")
            return {
                "ok": False,
                "error": "oecd_test_failed",
                "message": "Ошибка проверки OECD, подробности в логах backend",
            }

    if provider_id in PROVIDERS_WITH_API_KEY:
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


async def sync_all_enabled_providers(session: AsyncSession) -> dict:
    providers = await list_providers(session)
    enabled_ids = [provider.id for provider in providers if provider.enabled]
    if not enabled_ids:
        logger.info("scheduled_sync_skipped", reason="no_enabled_providers")
        return {"ok": True, "providers": [], "total_records": 0}

    results: list[dict] = []
    total_records = 0
    for provider_id in enabled_ids:
        result = await sync_provider(session, provider_id)
        result["provider_id"] = provider_id
        results.append(result)
        if result.get("ok"):
            total_records += int(result.get("records") or 0)
        logger.info(
            "scheduled_sync_provider",
            provider_id=provider_id,
            ok=result.get("ok"),
            records=result.get("records"),
            error=result.get("error"),
        )

    ok_count = sum(1 for result in results if result.get("ok"))
    return {
        "ok": ok_count == len(results),
        "providers": results,
        "total_records": total_records,
    }
