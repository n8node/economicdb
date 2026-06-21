from __future__ import annotations

from datetime import timedelta, timezone, tzinfo
from functools import lru_cache

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore[misc, assignment]


_FALLBACKS: dict[str, tzinfo] = {
    "Europe/Moscow": timezone(timedelta(hours=3)),
    "America/New_York": timezone(timedelta(hours=-5)),
    "Europe/Berlin": timezone(timedelta(hours=1)),
}


@lru_cache
def get_tz(name: str) -> tzinfo:
    if ZoneInfo is not None:
        try:
            return ZoneInfo(name)
        except Exception:
            pass
    fallback = _FALLBACKS.get(name)
    if fallback is not None:
        return fallback
    return timezone.utc


MSK = get_tz("Europe/Moscow")
ET = get_tz("America/New_York")
CET = get_tz("Europe/Berlin")
