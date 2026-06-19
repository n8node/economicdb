from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.indicators import get_db
from app.schemas.summaries import SummaryDetail, SummaryListResponse
from app.services import summaries as summaries_service

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.get("", response_model=SummaryListResponse)
async def list_summaries(
    region: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> SummaryListResponse:
    return await summaries_service.list_summaries(session, region=region)


@router.get("/latest", response_model=SummaryDetail)
async def latest_summary(session: AsyncSession = Depends(get_db)) -> SummaryDetail:
    data = await summaries_service.list_summaries(session)
    if not data.items:
        raise HTTPException(status_code=404, detail="summary_not_found")
    item = await summaries_service.get_summary(session, data.items[0].id)
    if item is None:
        raise HTTPException(status_code=404, detail="summary_not_found")
    return item


@router.get("/{summary_id}", response_model=SummaryDetail)
async def get_summary(summary_id: str, session: AsyncSession = Depends(get_db)) -> SummaryDetail:
    item = await summaries_service.get_summary(session, summary_id)
    if item is None:
        raise HTTPException(status_code=404, detail="summary_not_found")
    return item
