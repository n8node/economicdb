"""Smoke test for fedstatAPIr Python port."""
from __future__ import annotations

import asyncio
from datetime import date

from app.integrations.rosstat.fedstat import fetch_fedstat_series, fetch_fedstat_with_filters


async def main() -> None:
    to_date = date(2024, 12, 1)
    from_date = date(2024, 1, 1)

    legacy = await fetch_fedstat_series(
        "31074",
        series_key={"s_OKATO": "030", "s_grtov": "2", "s_POK": "9"},
        transform="index_yoy",
        from_date=from_date,
        to_date=to_date,
    )
    print("legacy GET points:", len(legacy), legacy[-3:])

    post = await fetch_fedstat_with_filters(
        "31074",
        filters={
            "Классификатор объектов административно-территориального деления (ОКАТО)": "Российская Федерация",
            "Виды показателя": "К соответствующему периоду предыдущего года",
            "Виды товаров и услуг": "Все товары и услуги",
        },
        transform="index_yoy",
        from_date=from_date,
        to_date=to_date,
    )
    print("POST points:", len(post), post[-3:])


if __name__ == "__main__":
    asyncio.run(main())
