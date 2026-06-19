import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.core.security import hash_password
from app.models.admin import AdminRole, AdminUser

logger = structlog.get_logger()


async def seed_super_admin(session: AsyncSession) -> None:
    count = await session.scalar(select(func.count()).select_from(AdminUser))
    if count and count > 0:
        logger.info("admin_seed_skipped", reason="admin_users not empty")
        return

    password = settings.admin_initial_password
    if not password:
        logger.warning("admin_seed_skipped", reason="ADMIN_INITIAL_PASSWORD not set")
        return

    admin = AdminUser(
        email=settings.admin_initial_email,
        password_hash=hash_password(password),
        role=AdminRole.SUPER_ADMIN.value,
    )
    session.add(admin)
    await session.commit()
    logger.info("super_admin_created", email=settings.admin_initial_email)
