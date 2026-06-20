"""List fedstat filter fields/values for indicator discovery."""
from __future__ import annotations

import asyncio
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.integrations.rosstat.fedstat_apir import fetch_data_ids


async def dump(indicator_id: str) -> None:
    rows = await fetch_data_ids(indicator_id)
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if row.filter_field_id == "0":
            continue
        grouped[row.filter_field_title].append(row.filter_value_title)
    print(f"=== {indicator_id} ===")
    for title, values in grouped.items():
        preview = values[:8]
        suffix = f" ... (+{len(values) - 8})" if len(values) > 8 else ""
        print(f"- {title}: {preview}{suffix}")


async def main() -> None:
    for indicator_id in sys.argv[1:] or ["31074", "57609", "31081", "57621", "57740", "31076"]:
        await dump(indicator_id)
        print()


if __name__ == "__main__":
    asyncio.run(main())
