from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.indicators import get_db
from app.schemas.dashboard import DashboardOverview
from app.services.dashboard import build_dashboard_overview
from app.services.summaries import dashboard_summary_teasers

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
async def dashboard_overview(session: AsyncSession = Depends(get_db)) -> DashboardOverview:
    current, previous = await dashboard_summary_teasers(session)
    return await build_dashboard_overview(session, ai_summary=current, previous_ai_summary=previous)
