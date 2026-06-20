from __future__ import annotations

from app.integrations.cbr.indicator_fetch import CBR_SOAP_SERIES
from app.integrations.rosstat.indicator_fetch import FEDSTAT_CONFIG, parse_fedstat_config_key
from app.models.indicators import Indicator

SUPPORTED_SOURCES = frozenset(
    {"cbr", "fred", "rosstat", "oecd", "imf", "ecb", "eurostat", "world_bank", "moex"}
)

CBR_FX_EXTERNAL_ID_LENGTHS = frozenset({6, 7})


def is_sync_ready(indicator: Indicator) -> bool:
    external_id = (indicator.external_id or "").strip()
    if not external_id:
        return False
    if "TODO" in external_id or "..." in external_id:
        return False
    if indicator.source not in SUPPORTED_SOURCES:
        return False
    if indicator.source == "cbr":
        if external_id == "KeyRate":
            return True
        if external_id.startswith("R") and len(external_id) in CBR_FX_EXTERNAL_ID_LENGTHS:
            return True
        return external_id in CBR_SOAP_SERIES
    if indicator.source == "rosstat":
        config_key = parse_fedstat_config_key(external_id)
        return config_key is not None and config_key in FEDSTAT_CONFIG
    if indicator.source == "oecd":
        if "/" in external_id:
            flow_key, series_key = external_id.split("/", 1)
            return bool(flow_key and series_key)
        return "." in external_id
    if indicator.source == "moex":
        parts = external_id.strip("/").split("/")
        return len(parts) == 4
    if indicator.source in {"world_bank", "imf"}:
        return "/" in external_id
    return True
