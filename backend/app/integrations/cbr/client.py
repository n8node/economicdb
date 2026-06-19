from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from html import unescape

import httpx
import structlog

logger = structlog.get_logger()

CBR_SOAP_URLS = (
    "https://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx",
    "http://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx",
    "https://cbr.ru/DailyInfoWebServ/DailyInfo.asmx",
    "http://cbr.ru/DailyInfoWebServ/DailyInfo.asmx",
)
CBR_NAMESPACE = "http://web.cbr.ru/"
DEFAULT_FROM_DATE = date(2020, 1, 1)


class CbrError(Exception):
    def __init__(self, message: str, *, code: str = "cbr_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _soap_envelope(action: str, inner_body: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    {inner_body}
  </soap:Body>
</soap:Envelope>"""


def _soap_datetime(value: date) -> str:
    return f"{value.isoformat()}T00:00:00"


async def _soap_call(action: str, inner_body: str) -> str:
    envelope = _soap_envelope(action, inner_body)
    errors: list[str] = []
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for url in CBR_SOAP_URLS:
            try:
                response = await client.post(
                    url,
                    content=envelope.encode("utf-8"),
                    headers={
                        "Content-Type": "text/xml; charset=utf-8",
                        "SOAPAction": f'"{CBR_NAMESPACE}{action}"',
                        "User-Agent": "economicdb/0.1 (+https://economicdb.com)",
                    },
                )
                if response.status_code >= 400:
                    errors.append(f"{url}: HTTP {response.status_code}")
                    continue
                logger.info("cbr_soap_call_ok", action=action, url=url)
                return response.text
            except httpx.TimeoutException:
                errors.append(f"{url}: timeout")
                logger.warning("cbr_soap_call_timeout", action=action, url=url)
            except httpx.HTTPError as exc:
                errors.append(f"{url}: {exc}")
                logger.warning("cbr_soap_call_failed", action=action, url=url, error=str(exc))

    if any("timeout" in error for error in errors):
        raise CbrError(f"ЦБ РФ не ответил за 30 секунд ({'; '.join(errors)})", code="cbr_timeout")
    raise CbrError(f"Не удалось подключиться к ЦБ РФ: {'; '.join(errors)}", code="cbr_network_error")


def _extract_result_xml(response_text: str, result_tag: str) -> str:
    match = re.search(rf"<{result_tag}>(.*?)</{result_tag}>", response_text, re.DOTALL)
    if not match:
        raise CbrError(f"Пустой ответ ЦБ ({result_tag})", code="cbr_empty_response")
    return unescape(match.group(1).strip())


def _parse_decimal(raw: str) -> Decimal | None:
    cleaned = raw.strip().replace(",", ".")
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _parse_observed(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    if "T" in value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return date.fromisoformat(value[:10])
    if "." in value:
        try:
            return datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _parse_key_rate_xml(xml_text: str) -> list[tuple[date, Decimal]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise CbrError("ЦБ РФ вернул некорректный XML для ключевой ставки", code="cbr_parse_error") from exc
    points: list[tuple[date, Decimal]] = []
    for node in root.iter():
        if node.tag.endswith("KR") or node.tag == "KR":
            dt_text = None
            rate_text = None
            for child in node:
                tag = child.tag.split("}")[-1]
                if tag == "DT":
                    dt_text = child.text
                elif tag == "Rate":
                    rate_text = child.text
            if not dt_text or not rate_text:
                continue
            observed = _parse_observed(dt_text)
            rate = _parse_decimal(rate_text)
            if observed is None or rate is None:
                continue
            points.append((observed, rate))
    return sorted(points, key=lambda item: item[0])


def _parse_dynamic_curs_xml(xml_text: str) -> list[tuple[date, Decimal]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise CbrError("ЦБ РФ вернул некорректный XML для курса валют", code="cbr_parse_error") from exc
    points: list[tuple[date, Decimal]] = []
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag != "Record":
            continue
        observed = _parse_observed(node.attrib.get("Date", ""))
        if observed is None:
            continue
        rate = _parse_decimal(node.attrib.get("VunitRate") or node.attrib.get("Value") or "")
        if rate is None:
            nominal_text = node.attrib.get("Nominal", "1")
            value_text = node.attrib.get("Value")
            nominal = _parse_decimal(nominal_text) or Decimal("1")
            total = _parse_decimal(value_text or "")
            if total is None or nominal == 0:
                continue
            rate = total / nominal
        points.append((observed, rate.quantize(Decimal("0.0001"))))
    return sorted(points, key=lambda item: item[0])


async def fetch_key_rate_series(
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    end = to_date or datetime.now(timezone.utc).date()
    inner = (
        f'<KeyRateXML xmlns="{CBR_NAMESPACE}">'
        f"<fromDate>{_soap_datetime(from_date)}</fromDate>"
        f"<ToDate>{_soap_datetime(end)}</ToDate>"
        f"</KeyRateXML>"
    )
    response = await _soap_call("KeyRateXML", inner)
    xml_text = _extract_result_xml(response, "KeyRateXMLResult")
    series = _parse_key_rate_xml(xml_text)
    if not series:
        raise CbrError("Не удалось разобрать ключевую ставку ЦБ", code="cbr_parse_error")
    return series


async def fetch_usd_rub_series(
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
    valuta_code: str = "R01235",
) -> list[tuple[date, Decimal]]:
    end = to_date or datetime.now(timezone.utc).date()
    inner = (
        f'<GetCursDynamicXML xmlns="{CBR_NAMESPACE}">'
        f"<FromDate>{_soap_datetime(from_date)}</FromDate>"
        f"<ToDate>{_soap_datetime(end)}</ToDate>"
        f"<ValutaCode>{valuta_code}</ValutaCode>"
        f"</GetCursDynamicXML>"
    )
    response = await _soap_call("GetCursDynamicXML", inner)
    xml_text = _extract_result_xml(response, "GetCursDynamicXMLResult")
    series = _parse_dynamic_curs_xml(xml_text)
    if not series:
        raise CbrError("Не удалось разобрать курс USD/RUB", code="cbr_parse_error")
    return series


async def test_connection() -> dict:
    today = datetime.now(timezone.utc).date()
    from_date = today - timedelta(days=30)
    key_rate = await fetch_key_rate_series(from_date=from_date, to_date=today)
    usd_rub = await fetch_usd_rub_series(from_date=from_date, to_date=today)
    key_date, key_value = key_rate[-1]
    usd_date, usd_value = usd_rub[-1]
    return {
        "key_rate_latest": {"date": key_date.isoformat(), "value": str(key_value)},
        "usd_rub_latest": {"date": usd_date.isoformat(), "value": str(usd_value)},
    }
