from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class SyncOptions:
    date_from: date | None = None
    date_to: date | None = None
    indicator_ids: list[str] | None = None
    country: str | None = None
    dry_run: bool = False
    trigger: str = "manual"
    admin_id: int | None = None
    job_id: int | None = None

    def allows_indicator(self, indicator_id: str) -> bool:
        if not self.indicator_ids:
            return True
        return indicator_id in self.indicator_ids

    def allows_country(self, country: str) -> bool:
        if not self.country:
            return True
        return country == self.country
