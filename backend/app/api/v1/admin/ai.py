import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_session
from app.models.admin import AdminUser
from app.schemas.admin_ai import DigestRegenerateRequest, DigestRegenerateResult
from app.services.digest import generate_and_store_weekly_digest

router = APIRouter(prefix="/admin/ai", tags=["admin-ai"])
logger = structlog.get_logger()


@router.post("/digest/regenerate", response_model=DigestRegenerateResult)
async def regenerate_weekly_digest(
    body: DigestRegenerateRequest,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> DigestRegenerateResult:
    result = await generate_and_store_weekly_digest(session, force=body.force)
    return DigestRegenerateResult(**result)
