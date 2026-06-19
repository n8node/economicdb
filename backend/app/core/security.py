from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
TOKEN_TTL_HOURS = 24


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_admin_token(admin_id: int, email: str, role: str) -> str:
    payload = {
        "sub": str(admin_id),
        "email": email,
        "role": role,
        "type": "admin",
        "exp": datetime.now(UTC) + timedelta(hours=TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
