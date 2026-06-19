import redis.asyncio as redis
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from alembic import command
from alembic.config import Config

from app.api.v1.router import api_router
from app.bootstrap.admin_seed import seed_super_admin
from app.bootstrap.indicator_seed import seed_real_indicators
from app.config.settings import settings
from app.db import SessionLocal, engine

structlog.configure(processors=[structlog.processors.JSONRenderer()])
logger = structlog.get_logger()


def run_migrations() -> None:
    alembic_cfg = Config("/app/alembic.ini")
    command.upgrade(alembic_cfg, "head")


async def check_redis() -> str:
    try:
        client = redis.from_url(settings.redis_url)
        await client.ping()
        await client.aclose()
        return "ok"
    except Exception:
        return "error"


def create_app() -> FastAPI:
    app = FastAPI(title="Макроаналитика API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.app_url, "http://localhost", "http://127.0.0.1"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup() -> None:
        run_migrations()
        async with SessionLocal() as session:
            await seed_super_admin(session)
            await seed_real_indicators(session)
        logger.info("startup_complete", environment=settings.environment)

    @app.get("/health")
    async def health() -> dict:
        pg_status = "ok"
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            pg_status = "error"

        redis_status = await check_redis()
        status = "ok" if pg_status == "ok" else "error"
        return {
            "status": status,
            "version": "0.1.0",
            "postgres": pg_status,
            "redis": redis_status,
        }

    @app.get("/api/v1/status")
    async def api_status() -> dict:
        return {"service": "macro-analytics", "ok": True}

    app.include_router(api_router)

    return app


app = create_app()
