from fastapi import APIRouter

from app.data.demo_dashboard import DEMO_OVERVIEW
from app.schemas.dashboard import DashboardOverview

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
async def dashboard_overview() -> DashboardOverview:
    return DEMO_OVERVIEW
