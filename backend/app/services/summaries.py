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


def _section_teaser(sections: dict, key: str, limit: int = 180) -> str | None:
    text = sections.get(key)
    if not isinstance(text, str) or not text.strip():
        return None
    cleaned = text.strip().replace("\n\n", " · ").replace("\n", " ")
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


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
        teaser = _section_teaser(sections, key)
        if teaser:
            bullets.append(teaser)
    if not bullets:
        bullets = [row.headline]
    return AiSummaryBlock(
        period=row.period_label,
        headline=row.headline,
        bullets=bullets[:3],
        summary_id=row.id,
    )
