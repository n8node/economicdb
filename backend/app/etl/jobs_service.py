from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.helpers import resolve_date_range
from app.etl.options import SyncOptions
from app.models.etl_jobs import EtlJob


def _serialize_ids(ids: list[str] | None) -> str | None:
    if not ids:
        return None
    return json.dumps(ids, ensure_ascii=False)


def _deserialize_ids(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


async def create_etl_job(session: AsyncSession, provider_id: str, options: SyncOptions | None) -> EtlJob:
    opts = options or SyncOptions()
    from_date, to_date = resolve_date_range(opts)
    job = EtlJob(
        provider_id=provider_id,
        trigger=opts.trigger,
        status="running",
        country=opts.country,
        indicator_ids=_serialize_ids(opts.indicator_ids),
        date_from=from_date,
        date_to=to_date,
        dry_run=opts.dry_run,
        admin_id=opts.admin_id,
    )
    session.add(job)
    await session.flush()
    return job


async def finish_etl_job(session: AsyncSession, job: EtlJob, result: dict) -> None:
    job.finished_at = datetime.now(timezone.utc)
    job.records = int(result.get("records") or 0)
    indicators = result.get("indicators") or []
    if isinstance(indicators, list):
        job.synced_indicators = json.dumps(indicators, ensure_ascii=False)
    if result.get("ok"):
        job.status = "ok"
        job.error_message = None
    else:
        job.status = "error"
        job.error_message = result.get("message") or result.get("error")


async def list_etl_jobs(
    session: AsyncSession,
    *,
    provider_id: str | None = None,
    limit: int = 50,
) -> list[EtlJob]:
    stmt = select(EtlJob).order_by(EtlJob.started_at.desc()).limit(limit)
    if provider_id:
        stmt = stmt.where(EtlJob.provider_id == provider_id)
    result = await session.scalars(stmt)
    return list(result.all())


def job_to_dict(job: EtlJob) -> dict:
    return {
        "id": job.id,
        "provider_id": job.provider_id,
        "trigger": job.trigger,
        "status": job.status,
        "country": job.country,
        "indicator_ids": _deserialize_ids(job.indicator_ids),
        "date_from": job.date_from.isoformat() if job.date_from else None,
        "date_to": job.date_to.isoformat() if job.date_to else None,
        "dry_run": job.dry_run,
        "records": job.records,
        "synced_indicators": _deserialize_ids(job.synced_indicators),
        "error_message": job.error_message,
        "admin_id": job.admin_id,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }
