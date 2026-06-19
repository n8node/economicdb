from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class IndicatorListItem(BaseModel):
    id: str
    name_ru: str
    country: str
    category: str
    frequency: str
    source: str
    unit: str | None
    last_value: str | None
    last_change: str | None
    delta_direction: str  # up | down | flat
    updated_at: datetime
    sparkline: list[float] = Field(default_factory=list)


class IndicatorDetail(IndicatorListItem):
    external_id: str | None = None


class IndicatorFacets(BaseModel):
    countries: dict[str, int]
    categories: dict[str, int]
    frequencies: dict[str, int]
    sources: dict[str, int]


class IndicatorListResponse(BaseModel):
    items: list[IndicatorListItem]
    total: int
    page: int
    page_size: int


class SeriesPoint(BaseModel):
    date: date
    value: float


class IndicatorSeriesResponse(BaseModel):
    indicator_id: str
    unit: str | None
    points: list[SeriesPoint]


class IndicatorSearchItem(BaseModel):
    id: str
    name_ru: str
    country: str
    source: str
