from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal


@dataclass(frozen=True)
class DemoIndicatorSeed:
    id: str
    name_ru: str
    country: str
    category: str
    frequency: str
    source: str
    unit: str
    base_value: Decimal
    step: Decimal


DEMO_INDICATORS: list[DemoIndicatorSeed] = [
    DemoIndicatorSeed("cbr_key_rate", "Ключевая ставка ЦБ", "ru", "rates", "monthly", "cbr", "%", Decimal("21.00"), Decimal("0")),
    DemoIndicatorSeed("ru_cpi_yoy", "ИПЦ России, г/г", "ru", "inflation", "monthly", "rosstat", "%", Decimal("9.52"), Decimal("0.08")),
    DemoIndicatorSeed("usd_rub", "USD / RUB", "ru", "fx", "daily", "cbr", "RUB", Decimal("92.40"), Decimal("0.35")),
    DemoIndicatorSeed("ru_gdp_yoy", "ВВП России, г/г", "ru", "gdp", "quarterly", "rosstat", "%", Decimal("4.10"), Decimal("0.05")),
    DemoIndicatorSeed("ru_unemployment", "Безработица, РФ", "ru", "labor", "monthly", "rosstat", "%", Decimal("2.60"), Decimal("-0.02")),
    DemoIndicatorSeed("ru_pmi", "PMI промышленности, РФ", "ru", "industry", "monthly", "rosstat", "index", Decimal("52.4"), Decimal("0.3")),
    DemoIndicatorSeed("us_cpi_yoy", "US CPI, г/г", "us", "inflation", "monthly", "fred", "%", Decimal("3.20"), Decimal("-0.03")),
    DemoIndicatorSeed("fed_funds", "Fed Funds Rate", "us", "rates", "monthly", "fred", "%", Decimal("5.375"), Decimal("0")),
    DemoIndicatorSeed("us_nfp", "Nonfarm Payrolls, США", "us", "labor", "monthly", "fred", "mln", Decimal("272.0"), Decimal("1.2")),
    DemoIndicatorSeed("us_gdp_yoy", "ВВП США, г/г", "us", "gdp", "quarterly", "fred", "%", Decimal("2.80"), Decimal("0.04")),
    DemoIndicatorSeed("eur_hicp_yoy", "HICP, еврозона, г/г", "eu", "inflation", "monthly", "oecd", "%", Decimal("2.10"), Decimal("-0.02")),
    DemoIndicatorSeed("ecb_rate", "Ставка ECB", "eu", "rates", "monthly", "oecd", "%", Decimal("4.00"), Decimal("0")),
    DemoIndicatorSeed("eur_usd", "EUR / USD", "eu", "fx", "daily", "oecd", "USD", Decimal("1.08"), Decimal("0.002")),
    DemoIndicatorSeed("cn_gdp_yoy", "ВВП Китая, г/г", "cn", "gdp", "quarterly", "oecd", "%", Decimal("5.20"), Decimal("0.03")),
    DemoIndicatorSeed("jp_cpi_yoy", "ИПЦ Японии, г/г", "jp", "inflation", "monthly", "oecd", "%", Decimal("2.80"), Decimal("0.01")),
    DemoIndicatorSeed("tr_policy_rate", "Ставка CBRT", "tr", "rates", "monthly", "oecd", "%", Decimal("50.00"), Decimal("0")),
    DemoIndicatorSeed("oil_brent", "Нефть Brent", "world", "commodities", "daily", "fred", "USD", Decimal("82.50"), Decimal("0.8")),
    DemoIndicatorSeed("global_pmi", "Global PMI", "world", "industry", "monthly", "oecd", "index", Decimal("50.8"), Decimal("0.1")),
]


def _months_back(start: date, count: int) -> list[date]:
    points: list[date] = []
    year, month = start.year, start.month
    for _ in range(count):
        points.append(date(year, month, 1))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(points))


def generate_series(seed: DemoIndicatorSeed, count: int = 24) -> list[tuple[date, Decimal]]:
    end = date(2026, 6, 1)
    if seed.frequency == "daily":
        return [(end - timedelta(days=i), seed.base_value + seed.step * Decimal(i % 5)) for i in range(count)][::-1]
    if seed.frequency == "quarterly":
        dates = []
        y, m = end.year, end.month
        for _ in range(count):
            q_month = ((m - 1) // 3) * 3 + 1
            dates.append(date(y, q_month, 1))
            m -= 3
            if m <= 0:
                m += 12
                y -= 1
        dates = list(reversed(dates))
    else:
        dates = _months_back(end, count)
    values: list[tuple[date, Decimal]] = []
    value = seed.base_value - seed.step * Decimal(count // 2)
    for idx, observed in enumerate(dates):
        drift = seed.step * Decimal(idx % 4)
        values.append((observed, value + drift))
    values[-1] = (dates[-1], seed.base_value)
    return values
