from datetime import date, datetime

from pydantic import BaseModel


class SummaryListItem(BaseModel):
    id: str
    period_label: str
    headline: str
    tags: list[str]
    word_count: int
    source_count: int
    generated_at: datetime
    status: str


class SummaryListResponse(BaseModel):
    items: list[SummaryListItem]
    total: int


class SummaryDetail(BaseModel):
    id: str
    period_label: str
    headline: str
    sections: dict[str, str]
    citations: dict[str, dict]
    tags: list[str]
    word_count: int
    source_count: int
    generated_at: datetime
    status: str
    reading_minutes: int
