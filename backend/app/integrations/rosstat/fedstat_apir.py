"""Python port of fedstatAPIr workflow (https://github.com/DenchPokepon/fedstatAPIr, MIT).

fedstatAPIr is an R package; we reuse its POST-based EMISS API approach in async Python.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass

import httpx
import structlog

from app.integrations.rosstat.client import HTTP_HEADERS, HTTP_RETRIES, HTTP_TIMEOUT, RosstatError

logger = structlog.get_logger()

FEDSTAT_DATA_URL = "https://www.fedstat.ru/indicator/data.do"
FEDSTAT_INDICATOR_URL = "https://www.fedstat.ru/indicator/{indicator_id}"

_QUOTE_FIX_RE = re.compile(r"\b(?=([^']*'[^']*')*[^']*$)")


@dataclass(frozen=True)
class DataIdRow:
    filter_field_id: str
    filter_field_title: str
    filter_value_id: str
    filter_value_title: str
    filter_field_object_ids: str


def _normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", value.strip())


def _str_norm(value: str) -> str:
    return re.sub(r"\s+", " ", _normalize_text(value).lower())


def _fedstat_headers(indicator_id: str) -> dict[str, str]:
    return {
        **HTTP_HEADERS,
        "Accept": "application/xml,text/xml,*/*",
        "Referer": FEDSTAT_INDICATOR_URL.format(indicator_id=indicator_id),
    }


def _js_object_to_json(text: str) -> dict:
    fixed = _QUOTE_FIX_RE.sub("'", text)
    fixed = fixed.replace("'", '"')
    return json.loads("{" + fixed + "}")


def _parse_js1(script_lines: list[str]) -> dict:
    start = next(i for i, line in enumerate(script_lines) if "filters: {" in line) + 1
    end = next(i for i, line in enumerate(script_lines) if "left_columns: [" in line) - 2
    chunk = "\n".join(script_lines[start : end + 1])
    return _js_object_to_json(chunk)


def _parse_js2(script_lines: list[str]) -> dict[str, str]:
    start = next(i for i, line in enumerate(script_lines) if "left_columns: [" in line)
    end = next(i for i, line in enumerate(script_lines) if "grid.init();" in line) - 2
    chunk = "\n".join(script_lines[start : end + 1])
    raw = _js_object_to_json(chunk)
    rename = {
        "left_columns": "lineObjectIds",
        "top_columns": "columnObjectIds",
        "groups": "lineObjectIds",
        "filterObjectIds": "lineObjectIds",
    }
    object_ids: dict[str, str] = {}
    for key, values in raw.items():
        bucket = rename.get(key, key)
        for field_id in values:
            object_ids[str(field_id)] = bucket
    if "0" not in object_ids.values():
        object_ids["0"] = "filterObjectIds"
    return object_ids


def _extract_grid_script(html: str) -> list[str]:
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.DOTALL | re.IGNORECASE)
    for script in scripts:
        if "filters: {" in script and "left_columns: [" in script:
            return script.splitlines()
    raise RosstatError("Не найден JS с фильтрами fedstat", code="rosstat_parse_error")


def parse_data_ids_from_html(indicator_id: str, html: str) -> list[DataIdRow]:
    script_lines = _extract_grid_script(html)
    filters = _parse_js1(script_lines)
    object_ids = _parse_js2(script_lines)

    rows: list[DataIdRow] = []
    for field_id, payload in filters.items():
        title = str(payload.get("title", ""))
        values = payload.get("values") or {}
        if not isinstance(values, dict) or not values:
            raise RosstatError(
                f"fedstat вернул пустые значения фильтра «{title}»",
                code="rosstat_parse_error",
            )
        object_id = object_ids.get(str(field_id), "lineObjectIds")
        for value_id, value_payload in values.items():
            value_title = str(value_payload.get("title", "")).replace("&quot;", '"')
            rows.append(
                DataIdRow(
                    filter_field_id=str(field_id),
                    filter_field_title=title,
                    filter_value_id=str(value_id),
                    filter_value_title=value_title,
                    filter_field_object_ids=object_id,
                )
            )
    return rows


async def fetch_indicator_html(indicator_id: str) -> str:
    headers = _fedstat_headers(indicator_id)
    errors: list[str] = []
    url = FEDSTAT_INDICATOR_URL.format(indicator_id=indicator_id)
    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            async with httpx.AsyncClient(
                timeout=HTTP_TIMEOUT,
                follow_redirects=True,
                headers=headers,
                trust_env=False,
            ) as client:
                response = await client.get(url)
            if response.status_code >= 400:
                errors.append(f"HTTP {response.status_code}")
                break
            return response.text
        except httpx.TimeoutException:
            errors.append(f"timeout (attempt {attempt})")
        except httpx.HTTPError as exc:
            errors.append(str(exc))
            break
    if any("timeout" in item for item in errors):
        raise RosstatError("fedstat.ru не ответил вовремя", code="rosstat_timeout")
    raise RosstatError(f"Не удалось загрузить страницу fedstat ({'; '.join(errors)})", code="rosstat_network_error")


_DATA_IDS_CACHE: dict[str, tuple[DataIdRow, ...]] = {}


async def fetch_data_ids(indicator_id: str) -> list[DataIdRow]:
    cached = _DATA_IDS_CACHE.get(indicator_id)
    if cached is not None:
        return list(cached)
    html = await fetch_indicator_html(indicator_id)
    rows = tuple(parse_data_ids_from_html(indicator_id, html))
    _DATA_IDS_CACHE[indicator_id] = rows
    return list(rows)


def filter_data_ids(
    data_ids: list[DataIdRow],
    filters: dict[str, str | list[str]],
) -> list[DataIdRow]:
    if not data_ids:
        raise RosstatError("Пустой список data_ids fedstat", code="rosstat_parse_error")

    normalized_filters: dict[str, list[str]] = {}
    for key, value in filters.items():
        if isinstance(value, str):
            normalized_filters[_str_norm(key)] = [_str_norm(value)]
        else:
            normalized_filters[_str_norm(key)] = [_str_norm(item) for item in value]

    rows_by_field: dict[str, list[DataIdRow]] = {}
    field_titles: dict[str, str] = {}
    for row in data_ids:
        rows_by_field.setdefault(row.filter_field_id, []).append(row)
        field_titles[row.filter_field_id] = row.filter_field_title

    indicator_title = next(
        (row.filter_value_title for row in data_ids if row.filter_field_id == "0"),
        "",
    )
    normalized_filters.setdefault(_str_norm("Показатель"), [_str_norm(indicator_title)])

    filtered_by_field: dict[str, list[DataIdRow]] = {}
    for field_id, rows in rows_by_field.items():
        field_norm = _str_norm(field_titles[field_id])
        if field_norm in normalized_filters:
            wanted = normalized_filters[field_norm]
            if wanted == ["*"]:
                filtered_by_field[field_id] = rows
                continue
            matched = [row for row in rows if _str_norm(row.filter_value_title) in wanted]
            if not matched:
                raise RosstatError(
                    f"Не найдены значения фильтра «{field_titles[field_id]}»",
                    code="rosstat_unconfigured",
                )
            filtered_by_field[field_id] = matched
            continue
        if len(rows) == 1:
            filtered_by_field[field_id] = rows
        else:
            filtered_by_field[field_id] = rows

    result: list[DataIdRow] = []
    for field_id in sorted(filtered_by_field):
        result.extend(filtered_by_field[field_id])
    return result


async def post_data_ids_filtered(
    data_ids: list[DataIdRow],
    *,
    indicator_id: str,
    data_format: str = "sdmx",
) -> str:
    indicator = next(row for row in data_ids if row.filter_field_id == "0")
    filters = {(row.filter_field_id, row.filter_field_object_ids) for row in data_ids if row.filter_field_id != "0"}

    body: list[tuple[str, str]] = [
        ("format", data_format),
        ("id", indicator.filter_value_id),
        ("indicator_title", indicator.filter_value_title),
    ]
    for field_id, object_ids in sorted(filters, key=lambda item: item[0]):
        body.append((object_ids, field_id))
    for row in data_ids:
        if row.filter_field_id == "0":
            continue
        body.append(("selectedFilterIds", f"{row.filter_field_id}_{row.filter_value_id}"))

    post_url = f"{FEDSTAT_DATA_URL}?format={data_format}"
    headers = _fedstat_headers(indicator_id)
    errors: list[str] = []
    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            async with httpx.AsyncClient(
                timeout=HTTP_TIMEOUT,
                follow_redirects=True,
                headers=headers,
                trust_env=False,
            ) as client:
                response = await client.post(post_url, data=body)
            if response.status_code >= 400:
                errors.append(f"HTTP {response.status_code}")
                break
            content_type = response.headers.get("content-type", "")
            text = response.content.decode("utf-8", errors="replace")
            if "text/xml" not in content_type and "<GenericData" not in text:
                errors.append("fedstat вернул не SDMX")
                break
            logger.info(
                "fedstat_post_ok",
                indicator_id=indicator_id,
                attempt=attempt,
                bytes=len(response.content),
            )
            return text
        except httpx.TimeoutException:
            errors.append(f"timeout (attempt {attempt})")
        except httpx.HTTPError as exc:
            errors.append(str(exc))
            break
    if any("timeout" in item for item in errors):
        raise RosstatError("fedstat.ru не ответил вовремя", code="rosstat_timeout")
    raise RosstatError(f"Не удалось POST fedstat ({'; '.join(errors)})", code="rosstat_network_error")


async def load_sdmx_with_filters(indicator_id: str, filters: dict[str, str | list[str]]) -> str:
    data_ids = await fetch_data_ids(indicator_id)
    filtered = filter_data_ids(data_ids, filters)
    return await post_data_ids_filtered(filtered, indicator_id=indicator_id)
