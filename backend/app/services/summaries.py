from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.summaries import WeeklySummary
from app.schemas.summaries import SummaryDetail, SummaryListItem, SummaryListResponse


async def list_summaries(
    session: AsyncSession,
    *,
    region: str | None = None,
) -> SummaryListResponse:
    query = select(WeeklySummary).order_by(WeeklySummary.period_start.desc())
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
    if row is None:
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


async def latest_summary_teaser(session: AsyncSession):
    row = await session.scalar(select(WeeklySummary).order_by(WeeklySummary.period_start.desc()).limit(1))
    if row is None:
        return None
    from app.schemas.dashboard import AiSummaryBlock

    bullets = [row.sections.get("ru", ""), row.sections.get("us", ""), row.sections.get("next_week", "")]
    bullets = [b for b in bullets if b][:3]
    return AiSummaryBlock(period=row.period_label, headline=row.headline, bullets=bullets or [row.headline])
