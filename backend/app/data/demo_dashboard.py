from app.schemas.dashboard import (
    AiSummaryBlock,
    CalendarEventItem,
    ChangeItem,
    DashboardOverview,
    FavoriteItem,
    KpiItem,
)

DEMO_OVERVIEW = DashboardOverview(
    updated_at="19.06.2026, 09:14 МСК",
    kpis=[
        KpiItem(label="Ключевая ставка ЦБ", value="21,00%", delta="0 п.п.", delta_direction="flat"),
        KpiItem(label="Инфляция РФ, г/г", value="9,52%", delta="+0,64 п.п.", delta_direction="up"),
        KpiItem(label="USD / RUB", value="92,40", delta="+1,2%", delta_direction="up"),
        KpiItem(label="US CPI, г/г", value="3,2%", delta="−0,1 п.п.", delta_direction="down"),
        KpiItem(label="Fed Funds Rate", value="5,25–5,50%", delta="0 п.п.", delta_direction="flat"),
    ],
    ai_summary=AiSummaryBlock(
        period="16–22 июня 2026",
        headline="ЦБ удержал ставку, инфляция в США замедлилась сильнее ожиданий",
        bullets=[
            "Банк России сохранил ключевую ставку на уровне 21% пятое заседание подряд",
            "Инфляция в США замедлилась сильнее консенсус-прогноза рынка",
            "На следующей неделе — заседание ECB и публикация промпроизводства РФ",
        ],
    ),
    calendar_events=[
        CalendarEventItem(title="Заседание ECB", time="23 июня, 15:45 МСК", country="eu"),
        CalendarEventItem(title="Промпроизводство РФ", time="24 июня, 10:00 МСК", country="ru"),
        CalendarEventItem(title="US PCE Index", time="26 июня, 15:30 МСК", country="us"),
    ],
    favorites=[
        FavoriteItem(
            label="ИПЦ России, г/г",
            value="9,52%",
            delta="+0,64 п.п.",
            delta_direction="up",
            source="rosstat",
        ),
        FavoriteItem(
            label="Ставка ЦБ РФ",
            value="21,00%",
            delta="0 п.п.",
            delta_direction="flat",
            source="cbr",
        ),
        FavoriteItem(
            label="US CPI, г/г",
            value="3,2%",
            delta="−0,1 п.п.",
            delta_direction="down",
            source="fred",
        ),
        FavoriteItem(
            label="EUR HICP, г/г",
            value="2,1%",
            delta="−0,1 п.п.",
            delta_direction="down",
            source="oecd",
        ),
    ],
    changes=[
        ChangeItem(
            direction="down",
            text="ИПЦ США вышел ниже консенсус-прогноза на 0,2 п.п.",
            meta="FRED · 19 июня 2026",
        ),
        ChangeItem(
            direction="up",
            text="Курс USD/RUB вырос на 1,2% за неделю",
            meta="Банк России · 19 июня 2026",
        ),
        ChangeItem(
            direction="flat",
            text="Ключевая ставка ЦБ РФ удержана пятое заседание подряд",
            meta="Банк России · 17 июня 2026",
        ),
    ],
)
