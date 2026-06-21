from __future__ import annotations

import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_json, encrypt_json
from app.models.settings import SystemSetting

DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = "openrouter.api_key"
OPENROUTER_BASE_URL = "openrouter.base_url"
OPENROUTER_MODEL_DIGEST = "openrouter.model_digest"
OPENROUTER_MODEL_FALLBACK = "openrouter.model_fallback"
OPENROUTER_META = "openrouter.meta"

_CACHE_TTL_SECONDS = 300
_cache: dict[str, tuple[float, Any]] = {}


def _cache_get(key: str) -> Any | None:
    item = _cache.get(key)
    if item is None:
        return None
    expires_at, value = item
    if time.monotonic() >= expires_at:
        _cache.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (time.monotonic() + _CACHE_TTL_SECONDS, value)


def invalidate_settings_cache(prefix: str | None = None) -> None:
    if prefix is None:
        _cache.clear()
        return
    for key in list(_cache):
        if key.startswith(prefix):
            _cache.pop(key, None)


def _unwrap(value: dict[str, Any]) -> str | None:
    raw = value.get("value")
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


async def get_setting(session: AsyncSession, key: str) -> str | None:
    cached = _cache_get(f"setting:{key}")
    if cached is not None:
        return cached

    row = await session.get(SystemSetting, key)
    if row is None:
        return None
    try:
        value = _unwrap(decrypt_json(row.value_encrypted))
    except ValueError:
        return None
    _cache_set(f"setting:{key}", value)
    return value


async def get_setting_json(session: AsyncSession, key: str) -> dict[str, Any]:
    cached = _cache_get(f"setting-json:{key}")
    if cached is not None:
        return cached

    row = await session.get(SystemSetting, key)
    if row is None:
        return {}
    try:
        data = decrypt_json(row.value_encrypted)
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}
    _cache_set(f"setting-json:{key}", data)
    return data


async def set_setting(
    session: AsyncSession,
    key: str,
    value: str,
    *,
    updated_by: int | None = None,
) -> None:
    row = await session.get(SystemSetting, key)
    payload = encrypt_json({"value": value})
    if row is None:
        row = SystemSetting(key=key, value_encrypted=payload, updated_by=updated_by)
        session.add(row)
    else:
        row.value_encrypted = payload
        row.updated_by = updated_by
    await session.commit()
    invalidate_settings_cache(None)


async def set_setting_json(
    session: AsyncSession,
    key: str,
    data: dict[str, Any],
    *,
    updated_by: int | None = None,
) -> None:
    row = await session.get(SystemSetting, key)
    payload = encrypt_json(data)
    if row is None:
        row = SystemSetting(key=key, value_encrypted=payload, updated_by=updated_by)
        session.add(row)
    else:
        row.value_encrypted = payload
        row.updated_by = updated_by
    await session.commit()
    invalidate_settings_cache("setting-json:")


async def delete_setting(session: AsyncSession, key: str) -> None:
    row = await session.get(SystemSetting, key)
    if row is None:
        return
    await session.delete(row)
    await session.commit()
    invalidate_settings_cache(None)


async def get_openrouter_api_key(session: AsyncSession, inline_key: str | None = None) -> str | None:
    if inline_key and inline_key.strip():
        return inline_key.strip()
    return await get_setting(session, OPENROUTER_API_KEY)


async def get_openrouter_base_url(session: AsyncSession, inline_base_url: str | None = None) -> str:
    if inline_base_url and inline_base_url.strip():
        return inline_base_url.strip().rstrip("/")
    stored = await get_setting(session, OPENROUTER_BASE_URL)
    return stored or DEFAULT_OPENROUTER_BASE_URL


async def load_openrouter_settings(session: AsyncSession) -> dict[str, Any]:
    api_key = await get_setting(session, OPENROUTER_API_KEY)
    base_url = await get_openrouter_base_url(session)
    model_digest = await get_setting(session, OPENROUTER_MODEL_DIGEST)
    model_fallback = await get_setting(session, OPENROUTER_MODEL_FALLBACK)
    meta = await get_setting_json(session, OPENROUTER_META)
    return {
        "has_api_key": bool(api_key),
        "base_url": base_url,
        "model_digest": model_digest,
        "model_fallback": model_fallback,
        "last_test_at": meta.get("last_test_at"),
        "last_test_status": meta.get("last_test_status"),
    }
