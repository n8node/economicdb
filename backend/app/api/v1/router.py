from fastapi import APIRouter

from app.api.v1.admin.auth import router as admin_auth_router
from app.api.v1.admin.providers import router as admin_providers_router
from app.api.v1.compare import router as compare_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.indicators import router as indicators_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(admin_auth_router)
api_router.include_router(admin_providers_router)
api_router.include_router(dashboard_router)
api_router.include_router(indicators_router)
api_router.include_router(compare_router)
