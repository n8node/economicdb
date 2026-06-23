from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.core.security import create_user_token, hash_password, verify_password
from app.models.admin import User
from app.schemas.user_auth import UserAuthResponse, UserLoginRequest, UserRegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        email_verified=user.email_verified,
        created_at=user.created_at,
    )


@router.post("/register", response_model=UserAuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(body: UserRegisterRequest, session: AsyncSession = Depends(get_session)) -> UserAuthResponse:
    existing = await session.scalar(select(User.id).where(User.email == body.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь с таким email уже зарегистрирован")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        personal_data_accepted_at=datetime.now(UTC),
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже зарегистрирован",
        ) from exc
    await session.refresh(user)

    token = create_user_token(user.id, user.email)
    return UserAuthResponse(access_token=token, user=user_response(user))


@router.post("/login", response_model=UserAuthResponse)
async def login_user(body: UserLoginRequest, session: AsyncSession = Depends(get_session)) -> UserAuthResponse:
    user = await session.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль")

    token = create_user_token(user.id, user.email)
    return UserAuthResponse(access_token=token, user=user_response(user))


@router.get("/me", response_model=UserResponse)
async def user_me(user: User = Depends(get_current_user)) -> UserResponse:
    return user_response(user)
