from pydantic import BaseModel, Field


class DigestRegenerateRequest(BaseModel):
    force: bool = Field(default=True)


class DigestRegenerateResult(BaseModel):
    ok: bool
    summary_id: str | None = None
    message: str | None = None
    error: str | None = None
    skipped: bool | None = None
    model: str | None = None
    word_count: int | None = None
    warnings: list[str] | None = None
