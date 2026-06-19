from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_json, encrypt_json
from app.models.providers import DataProvider


def has_stored_credentials(provider: DataProvider) -> bool:
    if not provider.credentials_encrypted:
        return False
    try:
        creds = decrypt_json(provider.credentials_encrypted)
    except ValueError:
        return False
    return bool(creds.get("api_key"))


def get_api_key(provider: DataProvider) -> str | None:
    if not provider.credentials_encrypted:
        return None
    creds = decrypt_json(provider.credentials_encrypted)
    key = creds.get("api_key")
    return key if isinstance(key, str) and key.strip() else None


async def save_api_key(session: AsyncSession, provider: DataProvider, api_key: str) -> None:
    provider.credentials_encrypted = encrypt_json({"api_key": api_key.strip()})
    await session.commit()
