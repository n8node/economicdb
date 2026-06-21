import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.summaries import WeeklySummary
from app.schemas.summaries import SummaryDetail, SummaryListItem, SummaryListResponse


async def list_summaries(
    session: AsyncSession,
    *,
    region: str | None = None,
) -> SummaryListResponse:
    query = (
        select(WeeklySummary)
        .where(WeeklySummary.status == "published")
        .order_by(WeeklySummary.period_start.desc())
    )
    rows = list((await session.scalars(query)).all())
    if region:
        rows = [r for r in rows if region in r.tags]
    items = [
        SummaryListItem(
            id=row.id,
            period_label=row.period_label,
            headline=row.headline,
            tags=row.tags,
            word_count=row.word_count,
            source_count=row.source_count,
            generated_at=row.generated_at,
            status=row.status,
        )
        for row in rows
    ]
    return SummaryListResponse(items=items, total=len(items))


async def get_summary(session: AsyncSession, summary_id: str) -> SummaryDetail | None:
    row = await session.get(WeeklySummary, summary_id)
    if row is None or row.status != "published":
        return None
    return SummaryDetail(
        id=row.id,
        period_label=row.period_label,
        headline=row.headline,
        sections=row.sections,
        citations=row.citations,
        tags=row.tags,
        word_count=row.word_count,
        source_count=row.source_count,
        generated_at=row.generated_at,
        status=row.status,
        reading_minutes=max(1, row.word_count // 200),
    )


def _truncate_teaser(text: str, limit: int = 150) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip(" ,.;:") + "…"


def _section_teasers(sections: dict, key: str, limit: int = 150) -> list[str]:
    text = sections.get(key)
    if not isinstance(text, str) or not text.strip():
        return []
    parts = [
        part.strip()
        for part in re.split(r"\n+|\s+•\s+", text.strip())
        if part.strip()
    ]
    if not parts:
        return []
    if len(parts) == 1:
        parts = [
            part.strip()
            for part in re.split(r"(?<=[.!?])\s+", parts[0])
            if part.strip()
        ]
    return [_truncate_teaser(part.lstrip("•").strip(), limit) for part in parts[:2]]


def _section_teaser(sections: dict, key: str, limit: int = 150) -> str | None:
    teasers = _section_teasers(sections, key, limit=limit)
    return teasers[0] if teasers else None


async def latest_summary_teaser(session: AsyncSession):
    row = await session.scalar(
        select(WeeklySummary)
        .where(WeeklySummary.status == "published")
        .order_by(WeeklySummary.period_start.desc())
        .limit(1)
    )
    if row is None:
        return None
    from app.schemas.dashboard import AiSummaryBlock

    sections = row.sections if isinstance(row.sections, dict) else {}
    bullets: list[str] = []
    for key in ("ru", "us", "next_week"):
        bullets.extend(_section_teasers(sections, key))
        if len(bullets) >= 4:
            break
    if not bullets:
        bullets = [row.headline]
    return AiSummaryBlock(
        period=row.period_label,
        headline=row.headline,
        bullets=bullets[:3],
        summary_id=row.id,
    )
