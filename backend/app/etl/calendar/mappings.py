from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from app.core.timezones import CET, ET, MSK


@dataclass(frozen=True)
class FredReleaseMapping:
    release_id: int
    slug: str
    title_ru: str
    country: str
    category: str
    importance: str
    linked_indicator_id: str | None
    unit: str | None = "%"


@dataclass(frozen=True)
class RosstatReleaseMapping:
    slug: str
    title_ru: str
    linked_indicator_id: str
    category: str
    importance: str
    day_of_month: int
    hour: int = 10
    minute: int = 0


FRED_RELEASE_MAPPINGS: list[FredReleaseMapping] = [
    FredReleaseMapping(10, "us_cpi", "ИПЦ США, г/г", "us", "inflation", "high", "us_cpi_yoy", "%"),
    FredReleaseMapping(50, "us_nfp", "Nonfarm Payrolls (занятость)", "us", "labor", "high", "us_nfp", "k"),
    FredReleaseMapping(54, "us_pce", "PCE, г/г", "us", "inflation", "high", "us_pce_yoy", "%"),
    FredReleaseMapping(53, "us_gdp", "ВВП США, г/г", "us", "gdp", "high", "us_gdp_yoy", "%"),
    FredReleaseMapping(13, "us_indpro", "Промышленное производство, США", "us", "industrial", "med", "us_indpro_yoy", "index"),
    FredReleaseMapping(46, "us_ppi", "PPI, г/г", "us", "inflation", "med", None, "%"),
    FredReleaseMapping(9, "us_retail", "Розничные продажи, США", "us", "consumption", "med", "us_retail_sales", "index"),
]

ROSSTAT_RELEASE_MAPPINGS: list[RosstatReleaseMapping] = [
    RosstatReleaseMapping("ru_cpi", "ИПЦ, г/г (Россия)", "ru_cpi_yoy", "inflation", "high", 10),
    RosstatReleaseMapping("ru_indpro", "Промышленное производство, г/г", "ru_industrial_yoy", "industrial", "high", 16),
    RosstatReleaseMapping("ru_retail", "Розничная торговля, г/г", "ru_retail_yoy", "consumption", "med", 22),
    RosstatReleaseMapping("ru_ppi", "Индекс цен производителей, г/г", "ru_ppi_yoy", "inflation", "med", 28),
]

TIER_A_EVENTS = {
    "cbr": {
        "slug": "cbr_key_rate",
        "title_ru": "Решение ЦБ по ключевой ставке",
        "country": "ru",
        "category": "rates",
        "importance": "high",
        "linked_indicator_id": "cbr_key_rate",
        "source": "cbr",
        "unit": "%",
        "hour": 13,
        "minute": 30,
    },
    "ecb": {
        "slug": "ecb_rate",
        "title_ru": "Заседание ECB по ставке",
        "country": "eu",
        "category": "rates",
        "importance": "high",
        "linked_indicator_id": "ecb_deposit_rate",
        "source": "ecb",
        "unit": "%",
        "hour": 16,
        "minute": 15,
    },
    "fomc": {
        "slug": "fomc_rate",
        "title_ru": "Заседание FOMC (ставка Fed)",
        "country": "us",
        "category": "rates",
        "importance": "high",
        "linked_indicator_id": "fed_funds",
        "source": "fred",
        "unit": "%",
        "hour": 21,
        "minute": 0,
    },
}


def us_release_datetime(day: date) -> datetime:
    dt_et = datetime.combine(day, time(8, 30), tzinfo=ET)
    return dt_et.astimezone(MSK)


def msk_datetime(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), tzinfo=MSK)


def event_id(source: str, slug: str, day: date) -> str:
    return f"{source}:{slug}:{day.isoformat()}"
