from __future__ import annotations

from app.integrations.rosstat.indicator_fetch import FEDSTAT_CONFIG, parse_fedstat_id
from app.models.indicators import Indicator

SUPPORTED_SOURCES = frozenset(
    {"cbr", "fred", "rosstat", "oecd", "imf", "ecb", "eurostat", "world_bank", "moex"}
)


def is_sync_ready(indicator: Indicator) -> bool:
    external_id = (indicator.external_id or "").strip()
    if not external_id:
        return False
    if indicator.source not in SUPPORTED_SOURCES:
        return False
    if indicator.source == "cbr":
        return external_id == "KeyRate" or (external_id.startswith("R") and len(external_id) == 6)
    if indicator.source == "rosstat":
        fedstat_id = parse_fedstat_id(external_id)
        return fedstat_id is not None and fedstat_id in FEDSTAT_CONFIG
    if indicator.source == "moex":
        parts = external_id.strip("/").split("/")
        return len(parts) == 4
    if indicator.source in {"world_bank", "imf"}:
        return "/" in external_id
    return True
