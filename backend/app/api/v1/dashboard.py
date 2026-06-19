from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.indicators import get_db
from app.data.demo_dashboard import DEMO_OVERVIEW
from app.schemas.dashboard import DashboardOverview
from app.services.dashboard import build_dashboard_overview
from app.services.summaries import latest_summary_teaser

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
async def dashboard_overview(session: AsyncSession = Depends(get_db)) -> DashboardOverview:
    try:
        teaser = await latest_summary_teaser(session)
        return await build_dashboard_overview(session, ai_summary=teaser or DEMO_OVERVIEW.ai_summary)
    except Exception:
        return DEMO_OVERVIEW
