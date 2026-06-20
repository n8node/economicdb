"""enable wave 2 indicators and wire remaining rosstat sources

Revision ID: 017
Revises: 016
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_INDICATORS: tuple[tuple[str, str, str, str, str, str, str, str], ...] = (
    ("de_hicp_yoy", "HICP Germany, г/г", "eu", "inflation", "monthly", "eurostat", "PRC_HICP_MANR/M.RCH_A.CP00.DE", "%"),
    ("us_pce_yoy", "PCE, г/г", "us", "inflation", "monthly", "fred", "PCEPI", "%"),
    ("jp_gdp_yoy_wb", "GDP growth (WB)", "jp", "gdp", "annual", "world_bank", "NY.GDP.MKTP.KD.ZG/JP", "%"),
    ("moex_rtsi", "Индекс RTS", "ru", "equities", "daily", "moex", "stock/index/RTSI/CLOSE", "index"),
    ("cn_gdp_wb", "GDP growth (WB)", "cn", "gdp", "annual", "world_bank", "NY.GDP.MKTP.KD.ZG/CN", "%"),
)

EXTERNAL_ID_UPDATES: dict[str, str] = {
    "ru_real_income_yoy": "fedstat:31094",
    "ru_real_wages_yoy": "fedstat:57849",
}

SOURCE_UPDATES: dict[str, tuple[str, str, str | None, str | None, str | None]] = {
    "ru_agriculture_yoy": (
        "world_bank",
        "NV.AGR.TOTL.KD.ZG/RU",
        "annual",
        "Сельхозпроизводство, г/г (WB)",
        "%",
    ),
    "ru_construction_yoy": (
        "world_bank",
        "NE.GDI.FIX.KD.ZG/RU",
        "annual",
        "Объём строительных работ, г/г (WB)",
        "%",
    ),
    "ru_exports_goods": (
        "world_bank",
        "NE.EXP.GNFS.KD.ZG/RU",
        "annual",
        "Экспорт товаров, г/г (WB)",
        "%",
    ),
    "ru_imports_goods": (
        "world_bank",
        "NE.IMP.GNFS.KD.ZG/RU",
        "annual",
        "Импорт товаров, г/г (WB)",
        "%",
    ),
}

ENABLE_INDICATORS: tuple[str, ...] = (
    "jpy_rub",
    "chf_rub",
    "try_rub",
    "kzt_rub",
    "byn_rub",
    "eu_core_hicp_yoy",
    "eu_food_hicp_yoy",
    "eu_energy_hicp_yoy",
    "de_hicp_yoy",
    "moex_usd_tom",
    "moex_eur_tom",
    "moex_rtsi",
    "vix",
    "us_pce_yoy",
    "jp_gdp_yoy_wb",
    "world_gdp_growth_wb",
    "oecd_cli_us",
    "oecd_cli_de",
    "in_inflation_wb",
    "cn_gdp_wb",
)


def upgrade() -> None:
    bind = op.get_bind()
    upsert = sa.text(
        """
        INSERT INTO indicators (
            id, name_ru, country, category, frequency, source, external_id, unit, enabled
        )
        VALUES (
            :id, :name_ru, :country, :category, :frequency, :source, :external_id, :unit, true
        )
        ON CONFLICT (id) DO UPDATE SET
            name_ru = EXCLUDED.name_ru,
            country = EXCLUDED.country,
            category = EXCLUDED.category,
            frequency = EXCLUDED.frequency,
            source = EXCLUDED.source,
            external_id = EXCLUDED.external_id,
            unit = EXCLUDED.unit
        """
    )
    for id_, name_ru, country, category, frequency, source, external_id, unit in NEW_INDICATORS:
        bind.execute(
            upsert,
            {
                "id": id_,
                "name_ru": name_ru,
                "country": country,
                "category": category,
                "frequency": frequency,
                "source": source,
                "external_id": external_id,
                "unit": unit,
            },
        )

    for indicator_id, external_id in EXTERNAL_ID_UPDATES.items():
        bind.execute(
            sa.text(
                """
                UPDATE indicators
                SET external_id = :external_id
                WHERE id = :indicator_id
                """
            ),
            {"external_id": external_id, "indicator_id": indicator_id},
        )

    for indicator_id, (source, external_id, frequency, name_ru, unit) in SOURCE_UPDATES.items():
        bind.execute(
            sa.text(
                """
                UPDATE indicators
                SET source = :source,
                    external_id = :external_id,
                    frequency = :frequency,
                    name_ru = :name_ru,
                    unit = :unit
                WHERE id = :indicator_id
                """
            ),
            {
                "source": source,
                "external_id": external_id,
                "frequency": frequency,
                "name_ru": name_ru,
                "unit": unit,
                "indicator_id": indicator_id,
            },
        )

    enable_stmt = sa.text("UPDATE indicators SET enabled = true WHERE id = :id")
    for indicator_id in ENABLE_INDICATORS:
        bind.execute(enable_stmt, {"id": indicator_id})


def downgrade() -> None:
    bind = op.get_bind()
    disable_stmt = sa.text("UPDATE indicators SET enabled = false WHERE id = :id")
    for indicator_id in ENABLE_INDICATORS:
        bind.execute(disable_stmt, {"id": indicator_id})
    for id_, *_ in NEW_INDICATORS:
        bind.execute(sa.text("DELETE FROM indicators WHERE id = :id"), {"id": id_})
