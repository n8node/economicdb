from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_session
from app.core.security import create_admin_token, verify_password
from app.models.admin import AdminUser
from app.schemas.admin_auth import AdminLoginRequest, AdminLoginResponse, AdminUserResponse

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(body: AdminLoginRequest, session: AsyncSession = Depends(get_session)) -> AdminLoginResponse:
    admin = await session.scalar(select(AdminUser).where(AdminUser.email == body.email))
    if admin is None or not verify_password(body.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")

    token = create_admin_token(admin.id, admin.email, admin.role)
    return AdminLoginResponse(
        access_token=token,
        admin=AdminUserResponse(id=admin.id, email=admin.email, role=admin.role),
    )


@router.get("/me", response_model=AdminUserResponse)
async def admin_me(admin: AdminUser = Depends(get_current_admin)) -> AdminUserResponse:
    return AdminUserResponse(id=admin.id, email=admin.email, role=admin.role)
