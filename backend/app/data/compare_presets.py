from __future__ import annotations

from datetime import date, timedelta

COMPARE_PRESETS: dict[str, dict] = {
    "rates": {
        "label": "Ставки ЦБ",
        "indicator_ids": ["cbr_key_rate", "fed_funds"],
    },
    "inflation": {
        "label": "Инфляция г/г",
        "indicator_ids": ["us_cpi_yoy"],
    },
    "fx": {
        "label": "Валюты и сырьё",
        "indicator_ids": ["usd_rub", "oil_brent"],
    },
    "gdp": {
        "label": "ВВП YoY",
        "indicator_ids": ["us_gdp_yoy"],
    },
}

PERIOD_DAYS = {
    "1M": 31,
    "3M": 92,
    "6M": 183,
    "1Y": 365,
    "3Y": 365 * 3,
    "5Y": 365 * 5,
}


def period_to_dates(period: str, date_to: date | None = None) -> tuple[date | None, date]:
    end = date_to or date.today()
    if period == "MAX":
        return None, end
    days = PERIOD_DAYS.get(period, 365)
    return end - timedelta(days=days), end
