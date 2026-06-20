from __future__ import annotations

from datetime import date

from app.integrations.cbr.client import (
    CbrError,
    fetch_international_reserves_series,
    fetch_key_rate_series,
    fetch_m2_series,
    fetch_mortgage_rate_series,
    fetch_usd_rub_series,
)
from app.models.indicators import Indicator

CBR_SOAP_SERIES = frozenset(
    {
        "SOAP:InternationalReserves",
        "SOAP:MoneySupply/M2",
    }
)
CBR_HTML_SERIES = frozenset({"HTML:MortgageRateAverage"})


async def fetch_indicator_series(
    indicator: Indicator,
    *,
    from_date: date,
    to_date: date,
) -> tuple[list[tuple[date, object]], str]:
    external_id = (indicator.external_id or "").strip()
    if not external_id:
        raise CbrError(f"Нет external_id для {indicator.id}", code="cbr_missing_external_id")

    if external_id == "KeyRate":
        series = await fetch_key_rate_series(from_date=from_date, to_date=to_date)
        return series, "KeyRate"

    if external_id.startswith("R") and len(external_id) in {6, 7}:
        series = await fetch_usd_rub_series(
            from_date=from_date,
            to_date=to_date,
            valuta_code=external_id,
        )
        return series, external_id

    if external_id == "SOAP:InternationalReserves":
        series = await fetch_international_reserves_series(from_date=from_date, to_date=to_date)
        return series, external_id

    if external_id == "SOAP:MoneySupply/M2":
        series = await fetch_m2_series(from_date=from_date, to_date=to_date)
        return series, external_id

    if external_id == "HTML:MortgageRateAverage":
        series = await fetch_mortgage_rate_series(from_date=from_date, to_date=to_date)
        return series, external_id

    raise CbrError(f"Неизвестный external_id ЦБ: {external_id}", code="cbr_unknown_external_id")
