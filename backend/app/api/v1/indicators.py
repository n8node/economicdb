from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.repositories import indicators as repo
from app.schemas.indicators import (
    IndicatorDetail,
    IndicatorFacets,
    IndicatorListResponse,
    IndicatorSearchItem,
    IndicatorSeriesResponse,
)

router = APIRouter(prefix="/indicators", tags=["indicators"])


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


@router.get("", response_model=IndicatorListResponse)
async def list_indicators(
    q: str | None = None,
    country: list[str] = Query(default=[]),
    category: list[str] = Query(default=[]),
    frequency: list[str] = Query(default=[]),
    source: list[str] = Query(default=[]),
    updated_within: int | None = Query(default=None, ge=1, le=365),
    sort: str = Query(default="name", pattern="^(name|updated|country)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> IndicatorListResponse:
    return await repo.list_indicators(
        session,
        q=q,
        country=country or None,
        category=category or None,
        frequency=frequency or None,
        source=source or None,
        updated_within_days=updated_within,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/facets", response_model=IndicatorFacets)
async def indicator_facets(session: AsyncSession = Depends(get_db)) -> IndicatorFacets:
    return await repo.get_facets(session)


@router.get("/facets/labels")
async def indicator_facet_labels() -> dict[str, dict[str, str]]:
    return repo.facet_labels()


@router.get("/search", response_model=list[IndicatorSearchItem])
async def search_indicators(
    q: str = Query(min_length=1),
    limit: int = Query(default=10, ge=1, le=20),
    session: AsyncSession = Depends(get_db),
) -> list[IndicatorSearchItem]:
    return await repo.search_indicators(session, q, limit)


@router.get("/{indicator_id}", response_model=IndicatorDetail)
async def get_indicator(indicator_id: str, session: AsyncSession = Depends(get_db)) -> IndicatorDetail:
    item = await repo.get_indicator(session, indicator_id)
    if item is None:
        raise HTTPException(status_code=404, detail="indicator_not_found")
    return item


@router.get("/{indicator_id}/series", response_model=IndicatorSeriesResponse)
async def get_indicator_series(
    indicator_id: str,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    session: AsyncSession = Depends(get_db),
) -> IndicatorSeriesResponse:
    series = await repo.get_series(session, indicator_id, date_from, date_to)
    if series is None:
        raise HTTPException(status_code=404, detail="indicator_not_found")
    return series
