from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class EtlSyncRequest(BaseModel):
    provider_id: str = Field(min_length=2, max_length=32)
    country: str | None = Field(default=None, max_length=8)
    indicator_ids: list[str] | None = None
    date_from: date | None = None
    date_to: date | None = None
    dry_run: bool = False


class EtlPreviewRequest(EtlSyncRequest):
    dry_run: bool = True


class EtlJobItem(BaseModel):
    id: int
    provider_id: str
    trigger: str
    status: str
    country: str | None = None
    indicator_ids: list[str] = Field(default_factory=list)
    date_from: str | None = None
    date_to: str | None = None
    dry_run: bool
    records: int | None = None
    synced_indicators: list[str] = Field(default_factory=list)
    error_message: str | None = None
    admin_id: int | None = None
    started_at: str | None = None
    finished_at: str | None = None


class EtlSyncResult(BaseModel):
    ok: bool
    provider_id: str | None = None
    job_id: int | None = None
    message: str | None = None
    records: int | None = None
    indicators: list[str] | None = None
    preview: list[dict] | None = None
    skipped: list[dict] | None = None
    error: str | None = None


class AdminIndicatorItem(BaseModel):
    id: str
    name_ru: str
    country: str
    category: str
    frequency: str
    source: str
    external_id: str | None = None
    unit: str | None = None
    last_value: str | None = None
    updated_at: str | None = None
    has_data: bool = False
    data_points: int = 0
    sync_ready: bool = False
    enabled: bool = True


class AdminIndicatorCreate(BaseModel):
    id: str = Field(min_length=2, max_length=64)
    name_ru: str = Field(min_length=2, max_length=255)
    country: str = Field(min_length=2, max_length=8)
    category: str = Field(min_length=2, max_length=64)
    frequency: str = Field(min_length=2, max_length=16)
    source: str = Field(min_length=2, max_length=32)
    external_id: str | None = Field(default=None, max_length=128)
    unit: str | None = Field(default=None, max_length=32)


class AdminIndicatorUpdate(BaseModel):
    name_ru: str | None = Field(default=None, min_length=2, max_length=255)
    category: str | None = Field(default=None, min_length=2, max_length=64)
    external_id: str | None = Field(default=None, max_length=128)
    unit: str | None = Field(default=None, max_length=32)
    enabled: bool | None = None


class CatalogTemplateItem(BaseModel):
    id: str
    name_ru: str
    country: str
    category: str
    frequency: str
    source: str
    external_id: str
    unit: str
    wave: str
    in_catalog: bool = False


class ImportTemplatesResult(BaseModel):
    imported: list[str]
    skipped: list[str]
