from datetime import datetime

from pydantic import BaseModel


class AdminUserItem(BaseModel):
    id: int
    email: str
    email_verified: bool
    personal_data_accepted_at: datetime
    created_at: datetime


class AdminUsersListResponse(BaseModel):
    items: list[AdminUserItem]
    total: int


class AdminUserDeleteResponse(BaseModel):
    ok: bool
    deleted_user_id: int
