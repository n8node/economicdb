from datetime import date

from pydantic import BaseModel, Field


class CompareSeriesRequest(BaseModel):
    indicator_ids: list[str] = Field(min_length=1, max_length=6)
    date_from: date | None = None
    date_to: date | None = None
    normalize: str = Field(default="absolute", pattern="^(absolute|index|change)$")


class CompareSeriesStats(BaseModel):
    min: float
    max: float
    avg: float
    change: float
    change_direction: str


class CompareSeriesItem(BaseModel):
    indicator_id: str
    name_ru: str
    country: str
    source: str
    unit: str | None
    values: list[float | None]
    last_value: str | None
    last_change: str | None
    delta_direction: str
    stats: CompareSeriesStats


class CompareSeriesResponse(BaseModel):
    labels: list[str]
    dates: list[date]
    series: list[CompareSeriesItem]
    unit_warning: bool
    axis_note: str
    normalize: str


class ComparePreset(BaseModel):
    key: str
    label: str
    indicator_ids: list[str]
