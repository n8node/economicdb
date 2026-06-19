from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.indicators import get_db
from app.schemas.compare import ComparePreset, CompareSeriesRequest, CompareSeriesResponse
from app.services import compare as compare_service

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("/presets", response_model=list[ComparePreset])
async def compare_presets() -> list[ComparePreset]:
    return compare_service.list_presets()


@router.post("/series", response_model=CompareSeriesResponse)
async def compare_series(
    body: CompareSeriesRequest,
    session: AsyncSession = Depends(get_db),
) -> CompareSeriesResponse:
    return await compare_service.build_compare_series(session, body)
