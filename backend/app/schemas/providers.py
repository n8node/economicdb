from pydantic import BaseModel, Field


class ProviderItem(BaseModel):
    id: str
    name_ru: str
    enabled: bool
    base_url: str | None = None
    has_credentials: bool = False
    supports_credentials: bool = False
    last_test_at: str | None = None
    last_test_status: str | None = None
    last_sync_at: str | None
    last_sync_status: str | None


class ProviderCredentialsUpdate(BaseModel):
    api_key: str = Field(min_length=8, max_length=256)


class ProviderUpdate(BaseModel):
    enabled: bool


class TestConnectionRequest(BaseModel):
    api_key: str | None = None


class TestConnectionResult(BaseModel):
    ok: bool
    message: str | None = None
    error: str | None = None
    details: dict | None = None


class SyncResult(BaseModel):
    ok: bool
    provider_id: str | None = None
    message: str | None = None
    records: int | None = None
    error: str | None = None
