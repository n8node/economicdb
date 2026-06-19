import asyncio

import redis.asyncio as redis
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alembic import command
from alembic.config import Config

from app.bootstrap.admin_seed import seed_super_admin
from app.config.settings import settings

structlog.configure(processors=[structlog.processors.JSONRenderer()])
logger = structlog.get_logger()


def _async_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(_async_database_url(settings.database_url), pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


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

    return app


app = create_app()
