from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_session
from app.models.admin import AdminUser, User
from app.schemas.admin_users import AdminUserDeleteResponse, AdminUserItem, AdminUsersListResponse

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def _user_item(user: User) -> AdminUserItem:
    return AdminUserItem(
        id=user.id,
        email=user.email,
        email_verified=user.email_verified,
        personal_data_accepted_at=user.personal_data_accepted_at,
        created_at=user.created_at,
    )


@router.get("", response_model=AdminUsersListResponse)
async def list_users(
    q: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminUsersListResponse:
    query = select(User)
    count_query = select(func.count()).select_from(User)

    search = q.strip() if q else ""
    if search:
        email_condition = User.email.ilike(f"%{search}%")
        condition = or_(email_condition, User.id == int(search)) if search.isdigit() else email_condition
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = await session.scalar(count_query)
    rows = await session.scalars(query.order_by(User.created_at.desc(), User.id.desc()).offset(offset).limit(limit))

    return AdminUsersListResponse(items=[_user_item(user) for user in rows], total=total or 0)


@router.get("/{user_id}", response_model=AdminUserItem)
async def get_user(
    user_id: int,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminUserItem:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return _user_item(user)


@router.delete("/{user_id}", response_model=AdminUserDeleteResponse)
async def delete_user(
    user_id: int,
    _: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> AdminUserDeleteResponse:
    result = await session.execute(delete(User).where(User.id == user_id))
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    await session.commit()
    return AdminUserDeleteResponse(ok=True, deleted_user_id=user_id)
