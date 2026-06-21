from pydantic import BaseModel, Field


class OpenRouterSettingsResponse(BaseModel):
    base_url: str
    has_api_key: bool
    model_digest: str | None = None
    model_fallback: str | None = None
    last_test_at: str | None = None
    last_test_status: str | None = None


class OpenRouterSettingsUpdate(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model_digest: str | None = None
    model_fallback: str | None = None


class OpenRouterTestRequest(BaseModel):
    api_key: str | None = None
    base_url: str | None = None


class OpenRouterTestResult(BaseModel):
    ok: bool
    message: str | None = None
    error: str | None = None
    models_count: int | None = None


class OpenRouterModelItem(BaseModel):
    id: str
    name: str
    label: str


class OpenRouterModelsResponse(BaseModel):
    items: list[OpenRouterModelItem] = Field(default_factory=list)


class OpenRouterModelsRequest(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
