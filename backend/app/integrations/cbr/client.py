from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from html import unescape
from typing import Iterator

import httpx
import structlog

logger = structlog.get_logger()

CBR_BASE_URL = "https://www.cbr.ru"
CBR_XML_DYNAMIC_URL = f"{CBR_BASE_URL}/scripts/XML_dynamic.asp"
CBR_KEY_RATE_URL = f"{CBR_BASE_URL}/hd_base/KeyRate/"
CBR_SOAP_URLS = (
    "http://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx",
    f"{CBR_BASE_URL}/DailyInfoWebServ/DailyInfo.asmx",
)
CBR_NAMESPACE = "http://web.cbr.ru/"
DEFAULT_FROM_DATE = date(2020, 1, 1)
CBR_HTTP_HEADERS = {
    "User-Agent": "economicdb/0.1 (+https://economicdb.com)",
    "Accept": "application/xml,text/xml,text/html,*/*",
}


class CbrError(Exception):
    def __init__(self, message: str, *, code: str = "cbr_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _format_cbr_date_slash(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _format_cbr_date_dot(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def _iter_year_chunks(from_date: date, to_date: date) -> Iterator[tuple[date, date]]:
    cursor = from_date
    while cursor <= to_date:
        chunk_end = min(date(cursor.year, 12, 31), to_date)
        yield cursor, chunk_end
        if chunk_end >= to_date:
            break
        cursor = date(cursor.year + 1, 1, 1)


def _soap_envelope(inner_body: str) -> str:
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


async def _http_get(
    url: str,
    params: dict[str, str] | None = None,
    *,
    encoding: str = "windows-1251",
    timeout: float = 45.0,
) -> str:
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers=CBR_HTTP_HEADERS,
        ) as client:
            response = await client.get(url, params=params)
    except httpx.TimeoutException as exc:
        raise CbrError("ЦБ РФ не ответил за 45 секунд", code="cbr_timeout") from exc
    except httpx.HTTPError as exc:
        raise CbrError(f"Не удалось подключиться к ЦБ РФ: {exc}", code="cbr_network_error") from exc

    if response.status_code >= 400:
        raise CbrError(
            f"ЦБ РФ вернул HTTP {response.status_code} для {url}",
            code="cbr_http_error",
        )

    if encoding:
        return response.content.decode(encoding, errors="replace")
    return response.text


async def _soap_call(action: str, inner_body: str) -> str:
    envelope = _soap_envelope(inner_body)
    errors: list[str] = []
    async with httpx.AsyncClient(timeout=45.0, follow_redirects=True, headers=CBR_HTTP_HEADERS) as client:
        for url in CBR_SOAP_URLS:
            try:
                response = await client.post(
                    url,
                    content=envelope.encode("utf-8"),
                    headers={
                        "Content-Type": "text/xml; charset=utf-8",
                        "SOAPAction": f'"{CBR_NAMESPACE}{action}"',
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
        raise CbrError(f"SOAP ЦБ РФ: timeout ({'; '.join(errors)})", code="cbr_timeout")
    raise CbrError(f"SOAP ЦБ РФ недоступен ({'; '.join(errors)})", code="cbr_network_error")


def _extract_result_xml(response_text: str, result_tag: str) -> str:
    match = re.search(rf"<{result_tag}>(.*?)</{result_tag}>", response_text, re.DOTALL)
    if not match:
        raise CbrError(f"Пустой SOAP-ответ ЦБ ({result_tag})", code="cbr_empty_response")
    return unescape(match.group(1).strip())


def _parse_decimal(raw: str) -> Decimal | None:
    cleaned = raw.strip().replace("\xa0", "").replace(" ", "").replace(",", ".")
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


def _parse_key_rate_html(html: str) -> list[tuple[date, Decimal]]:
    points: list[tuple[date, Decimal]] = []
    for match in re.finditer(
        r"<td[^>]*>\s*(\d{2}\.\d{2}\.\d{4})\s*</td>\s*<td[^>]*>\s*([\d,\.]+)\s*</td>",
        html,
        flags=re.IGNORECASE,
    ):
        observed = _parse_observed(match.group(1))
        rate = _parse_decimal(match.group(2))
        if observed is None or rate is None:
            continue
        points.append((observed, rate))
    return sorted(points, key=lambda item: item[0])


def _record_field(node: ET.Element, name: str) -> str | None:
    value = node.attrib.get(name)
    if value:
        return value
    for child in node:
        if child.tag.split("}")[-1] == name and child.text:
            return child.text.strip()
    return None


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
        observed = _parse_observed(_record_field(node, "Date") or node.attrib.get("Date", ""))
        if observed is None:
            continue
        rate = _parse_decimal(_record_field(node, "VunitRate") or _record_field(node, "Value") or "")
        if rate is None:
            nominal = _parse_decimal(_record_field(node, "Nominal") or "1") or Decimal("1")
            total = _parse_decimal(_record_field(node, "Value") or "")
            if total is None or nominal == 0:
                continue
            rate = total / nominal
        points.append((observed, rate.quantize(Decimal("0.0001"))))
    return sorted(points, key=lambda item: item[0])


async def _fetch_key_rate_soap(from_date: date, to_date: date) -> list[tuple[date, Decimal]]:
    inner = (
        f'<KeyRateXML xmlns="{CBR_NAMESPACE}">'
        f"<fromDate>{_soap_datetime(from_date)}</fromDate>"
        f"<ToDate>{_soap_datetime(to_date)}</ToDate>"
        f"</KeyRateXML>"
    )
    response = await _soap_call("KeyRateXML", inner)
    xml_text = _extract_result_xml(response, "KeyRateXMLResult")
    series = _parse_key_rate_xml(xml_text)
    if not series:
        raise CbrError("Не удалось разобрать ключевую ставку ЦБ (SOAP)", code="cbr_parse_error")
    return series


async def _fetch_key_rate_html(from_date: date, to_date: date) -> list[tuple[date, Decimal]]:
    html = await _http_get(
        CBR_KEY_RATE_URL,
        {
            "UniDbQuery.Posted": "True",
            "UniDbQuery.From": _format_cbr_date_dot(from_date),
            "UniDbQuery.To": _format_cbr_date_dot(to_date),
        },
        encoding="utf-8",
    )
    series = _parse_key_rate_html(html)
    if not series:
        raise CbrError("Не удалось разобрать ключевую ставку ЦБ (HTML)", code="cbr_parse_error")
    return series


async def _fetch_key_rate_chunk(from_date: date, to_date: date) -> list[tuple[date, Decimal]]:
    try:
        series = await _fetch_key_rate_soap(from_date, to_date)
        logger.info("cbr_key_rate_source", source="soap", from_date=from_date.isoformat(), to_date=to_date.isoformat())
        return series
    except CbrError as exc:
        logger.warning(
            "cbr_key_rate_soap_fallback",
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            error=exc.message,
        )
        series = await _fetch_key_rate_html(from_date, to_date)
        logger.info("cbr_key_rate_source", source="html", from_date=from_date.isoformat(), to_date=to_date.isoformat())
        return series


async def fetch_key_rate_series(
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
) -> list[tuple[date, Decimal]]:
    end = to_date or datetime.now(timezone.utc).date()
    merged: dict[date, Decimal] = {}
    for chunk_from, chunk_to in _iter_year_chunks(from_date, end):
        for observed, value in await _fetch_key_rate_chunk(chunk_from, chunk_to):
            merged[observed] = value
    series = sorted(merged.items(), key=lambda item: item[0])
    if not series:
        raise CbrError("Не удалось получить ключевую ставку ЦБ", code="cbr_parse_error")
    return series


async def fetch_usd_rub_series(
    *,
    from_date: date = DEFAULT_FROM_DATE,
    to_date: date | None = None,
    valuta_code: str = "R01235",
) -> list[tuple[date, Decimal]]:
    end = to_date or datetime.now(timezone.utc).date()
    merged: dict[date, Decimal] = {}
    for chunk_from, chunk_to in _iter_year_chunks(from_date, end):
        xml_text = await _http_get(
            CBR_XML_DYNAMIC_URL,
            {
                "date_req1": _format_cbr_date_slash(chunk_from),
                "date_req2": _format_cbr_date_slash(chunk_to),
                "VAL_NM_RQ": valuta_code,
            },
        )
        for observed, value in _parse_dynamic_curs_xml(xml_text):
            merged[observed] = value
    series = sorted(merged.items(), key=lambda item: item[0])
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
