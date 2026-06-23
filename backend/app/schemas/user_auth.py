from datetime import datetime
import re

from pydantic import BaseModel, EmailStr, Field, field_validator


def validate_password_strength(password: str) -> str:
    checks = [
        len(password) >= 8,
        re.search(r"[a-z]", password) is not None,
        re.search(r"[A-Z]", password) is not None,
        re.search(r"\d", password) is not None,
    ]
    if not all(checks):
        raise ValueError("Пароль должен содержать минимум 8 символов, строчную, заглавную букву и цифру")
    return password


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    personal_data_consent: bool

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return validate_password_strength(value)

    @field_validator("personal_data_consent")
    @classmethod
    def consent_required(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Необходимо согласие на обработку персональных данных")
        return value


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    id: int
    email: str
    email_verified: bool
    created_at: datetime


class UserAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
