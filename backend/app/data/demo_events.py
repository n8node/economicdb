from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True)
class DemoEventSeed:
    id: str
    title_ru: str
    country: str
    category: str
    importance: str
    scheduled_at_msk: datetime
    actual: Decimal | None
    forecast: Decimal | None
    previous: Decimal | None
    source: str
    unit: str | None
    linked_indicator_id: str | None = None


def _dt(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 6, day, hour, minute, tzinfo=timezone.utc)


DEMO_EVENTS: list[DemoEventSeed] = [
    DemoEventSeed("evt_ecb_jun23", "Заседание ECB", "eu", "rates", "high", _dt(23, 12, 45), None, None, Decimal("4.00"), "oecd", "%", "ecb_rate"),
    DemoEventSeed("evt_ru_ppi_jun24", "Промпроизводство РФ", "ru", "industry", "med", _dt(24, 7, 0), None, Decimal("3.1"), Decimal("2.8"), "rosstat", "%", "ru_pmi"),
    DemoEventSeed("evt_us_pce_jun26", "US PCE Index", "us", "inflation", "high", _dt(26, 12, 30), None, Decimal("2.6"), Decimal("2.7"), "fred", "%", "us_cpi_yoy"),
    DemoEventSeed("evt_cbr_jun17", "Решение ЦБ по ключевой ставке", "ru", "rates", "high", _dt(17, 13, 30), Decimal("21.00"), Decimal("21.00"), Decimal("21.00"), "cbr", "%", "cbr_key_rate"),
    DemoEventSeed("evt_us_cpi_jun12", "US CPI, м/м", "us", "inflation", "high", _dt(12, 12, 30), Decimal("0.1"), Decimal("0.2"), Decimal("0.2"), "fred", "%", "us_cpi_yoy"),
    DemoEventSeed("evt_ru_cpi_jun12", "ИПЦ РФ, м/м", "ru", "inflation", "high", _dt(12, 9, 0), Decimal("0.64"), Decimal("0.55"), Decimal("0.48"), "rosstat", "%", "ru_cpi_yoy"),
    DemoEventSeed("evt_fed_jun18", "Заседание FOMC", "us", "rates", "high", _dt(18, 18, 0), Decimal("5.375"), Decimal("5.375"), Decimal("5.375"), "fred", "%", "fed_funds"),
    DemoEventSeed("evt_eu_hicp_jun16", "HICP, еврозона", "eu", "inflation", "med", _dt(16, 11, 0), Decimal("2.1"), Decimal("2.2"), Decimal("2.2"), "oecd", "%", "eur_hicp_yoy"),
    DemoEventSeed("evt_us_nfp_jun6", "Nonfarm Payrolls", "us", "employment", "high", _dt(6, 12, 30), Decimal("272"), Decimal("185"), Decimal("165"), "fred", "k", "us_nfp"),
    DemoEventSeed("evt_ru_gdp_jun20", "ВВП РФ, предварительная оценка", "ru", "gdp", "med", _dt(20, 9, 0), Decimal("4.1"), Decimal("4.0"), Decimal("3.9"), "rosstat", "%", "ru_gdp_yoy"),
    DemoEventSeed("evt_usd_rub_jun19", "Официальный курс USD/RUB", "ru", "fx", "low", _dt(19, 12, 0), Decimal("92.40"), None, Decimal("91.20"), "cbr", "RUB", "usd_rub"),
    DemoEventSeed("evt_cn_gdp_jun25", "ВВП Китая, г/г", "cn", "gdp", "high", _dt(25, 4, 0), None, Decimal("5.1"), Decimal("5.0"), "oecd", "%", "cn_gdp_yoy"),
    DemoEventSeed("evt_jp_cpi_jun20", "ИПЦ Японии", "jp", "inflation", "med", _dt(20, 2, 30), Decimal("2.8"), Decimal("2.7"), Decimal("2.7"), "oecd", "%", "jp_cpi_yoy"),
]
