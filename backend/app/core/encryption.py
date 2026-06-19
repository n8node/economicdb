from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.config.settings import settings


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.settings_encryption_key.encode()).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_json(data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False).encode()
    return _fernet().encrypt(payload).decode()


def decrypt_json(token: str | None) -> dict[str, Any]:
    if not token:
        return {}
    try:
        payload = _fernet().decrypt(token.encode())
    except InvalidToken as exc:
        raise ValueError("invalid_credentials") from exc
    data = json.loads(payload.decode())
    if not isinstance(data, dict):
        raise ValueError("invalid_credentials")
    return data
