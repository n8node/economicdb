"""enable ru shortlist indicators

Revision ID: 021
Revises: 020
Create Date: 2026-06-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


RU_SHORTLIST: tuple[tuple[str, str, str, str, str, str, str, str], ...] = (
    ("eur_rub", "EUR / RUB", "ru", "fx", "daily", "cbr", "R01239", "RUB"),
    ("cny_rub", "CNY / RUB", "ru", "fx", "daily", "cbr", "R01375", "RUB"),
    ("gbp_rub", "GBP / RUB", "ru", "fx", "daily", "cbr", "R01035", "RUB"),
    ("ru_cpi_mom", "ИПЦ, м/м", "ru", "inflation", "monthly", "rosstat", "fedstat:31074/mom", "%"),
    ("ru_core_cpi_yoy", "Базовый ИПЦ, г/г", "ru", "inflation", "monthly", "rosstat", "fedstat:31081", "%"),
    ("ru_retail_yoy", "Розничная торговля, г/г", "ru", "consumption", "monthly", "rosstat", "fedstat:31066", "%"),
    ("ru_unemployment", "Безработица", "ru", "labor", "quarterly", "rosstat", "fedstat:43062", "%"),
    ("ru_gdp_q_yoy", "ВВП РФ, г/г", "ru", "gdp", "quarterly", "rosstat", "fedstat:31077", "%"),
    ("ru_wages_yoy", "Зарплаты, г/г", "ru", "labor", "monthly", "rosstat", "fedstat:57849", "%"),
    ("ru_gdp_yoy_imf", "ВВП РФ, real growth (IMF)", "ru", "gdp", "annual", "imf", "NGDP_RPCH/RUS", "%"),
    ("moex_rtsi", "Индекс RTS", "ru", "equities", "daily", "moex", "stock/index/RTSI/CLOSE", "index"),
    ("moex_rgbi", "Индекс гособлигаций RGBI", "ru", "rates", "daily", "moex", "stock/index/RGBI/CLOSE", "index"),
    ("moex_mcftr", "MOEX Total Return", "ru", "equities", "daily", "moex", "stock/index/MCFTR/CLOSE", "index"),
    ("moex_bluechip", "MOEX Blue Chip", "ru", "equities", "daily", "moex", "stock/index/MOEXBC/CLOSE", "index"),
    ("moex_usd_tom", "USD/RUB TOM (MOEX)", "ru", "fx", "daily", "moex", "currency/selt/USD000UTSTOM/CLOSE", "RUB"),
    ("moex_eur_tom", "EUR/RUB TOM (MOEX)", "ru", "fx", "daily", "moex", "currency/selt/EUR_RUB__TOM/CLOSE", "RUB"),
    ("ru_cpi_wb", "Инфляция РФ (WB)", "ru", "inflation", "annual", "world_bank", "FP.CPI.TOTL.ZG/RU", "%"),
    ("ru_unemp_wb", "Безработица РФ (WB)", "ru", "labor", "annual", "world_bank", "SL.UEM.TOTL.ZS/RU", "%"),
    ("ru_ca_wb", "Сальдо текущего счёта % ВВП (WB)", "ru", "external", "annual", "world_bank", "BN.CAB.XOKA.GD.ZS/RU", "% GDP"),
    ("ru_debt_wb", "Госдолг % ВВП (WB)", "ru", "fiscal", "annual", "world_bank", "GC.DOD.TOTL.GD.ZS/RU", "% GDP"),
    ("ru_fx_reserves", "Международные резервы РФ", "ru", "external", "monthly", "cbr", "SOAP:InternationalReserves", "USD bn"),
    ("ru_m2", "Денежная масса M2", "ru", "rates", "monthly", "cbr", "SOAP:MoneySupply/M2", "RUB bn"),
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
            unit = EXCLUDED.unit,
            enabled = true
        """
    )
    for id_, name_ru, country, category, frequency, source, external_id, unit in RU_SHORTLIST:
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


def downgrade() -> None:
    pass
