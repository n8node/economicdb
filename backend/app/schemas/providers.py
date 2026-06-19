from pydantic import BaseModel


class ProviderItem(BaseModel):
    id: str
    name_ru: str
    enabled: bool
    last_sync_at: str | None
    last_sync_status: str | None


class SyncResult(BaseModel):
    ok: bool
    provider_id: str | None = None
    message: str | None = None
    records: int | None = None
    error: str | None = None
