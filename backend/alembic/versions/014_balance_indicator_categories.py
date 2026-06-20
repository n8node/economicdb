"""add balanced indicator catalog wave and enable sync-ready rows

Revision ID: 014
Revises: 013
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_INDICATORS: tuple[tuple[str, str, str, str, str, str, str, str], ...] = (
    ("us_personal_income", "Личные доходы, США", "us", "income", "monthly", "fred", "PI", "USD bn"),
    ("us_real_personal_income", "Реальные личные доходы, США", "us", "income", "monthly", "fred", "RPI", "USD bn"),
    ("us_avg_hourly_earnings", "Средняя почасовая оплата, США", "us", "income", "monthly", "fred", "CES0500000003", "USD"),
    ("us_real_hourly_earnings", "Реальная почасовая оплата, США", "us", "income", "monthly", "fred", "COMPRNFB", "index"),
    ("us_wage_growth_yoy", "Рост заработной платы, г/г", "us", "income", "monthly", "fred", "AHETPI", "%"),
    ("ru_gdp_pc_wb", "ВВП на душу населения (WB)", "ru", "income", "annual", "world_bank", "NY.GDP.PCAP.KD/RU", "USD"),
    ("us_financial_stress", "Financial Stress Index (St. Louis Fed)", "us", "financial", "weekly", "fred", "STLFSI4", "index"),
    ("us_ted_spread", "TED spread", "us", "financial", "daily", "fred", "TEDRATE", "%"),
    ("us_baa_corporate_yield", "BAA corporate yield", "us", "financial", "daily", "fred", "BAMLC0A4CBBBEY", "%"),
    ("us_mortgage_30y", "Ипотека 30 лет, США", "us", "financial", "weekly", "fred", "MORTGAGE30US", "%"),
    ("us_lei", "Leading Economic Index, США", "us", "financial", "monthly", "fred", "USSLIND", "index"),
    ("us_ig_credit_spread", "Investment-grade credit spread", "us", "financial", "daily", "fred", "BAMLC0A0CM", "%"),
    ("us_housing_starts", "Housing starts, США", "us", "construction", "monthly", "fred", "HOUST", "thousand"),
    ("us_case_shiller_yoy", "Case-Shiller, г/г", "us", "construction", "monthly", "fred", "CSUSHPINSA", "%"),
    ("us_existing_home_sales", "Продажи существующего жилья, США", "us", "construction", "monthly", "fred", "EXHOSLUSM495S", "million"),
    (
        "eu_building_permits_yoy",
        "Разрешения на строительство EA, г/г",
        "eu",
        "construction",
        "monthly",
        "eurostat",
        "sts_cobp_m/M.I15.Y.PRCN.NS0030.EA20",
        "%",
    ),
    ("us_consumer_sentiment", "Consumer sentiment (Michigan)", "us", "consumption", "monthly", "fred", "UMCSENT", "index"),
    ("us_durable_goods_orders", "Заказы на товары длит. пользования", "us", "consumption", "monthly", "fred", "DGORDER", "USD mn"),
    ("us_vehicle_sales", "Продажи легковых авто, США", "us", "consumption", "monthly", "fred", "TOTALSA", "million"),
    ("oil_wti", "WTI crude", "world", "commodities", "daily", "fred", "DCOILWTICO", "USD/bbl"),
    ("nat_gas_us", "Природный газ Henry Hub", "world", "commodities", "daily", "fred", "DHHNGSP", "USD/MMBtu"),
    ("gold_spot", "Золото (London fix)", "world", "commodities", "daily", "fred", "GOLDAMGBD228NLBM", "USD/oz"),
    ("copper_price", "Медь, мировая цена", "world", "commodities", "monthly", "fred", "PCOPPUSDM", "USD/mt"),
    ("wheat_price", "Пшеница, мировая цена", "world", "commodities", "monthly", "fred", "PWHEAMTUSDM", "USD/mt"),
    ("us_manufacturing_ip_yoy", "Manufacturing IP, г/г", "us", "industrial", "monthly", "fred", "IPMAN", "%"),
    (
        "eu_industrial_production_yoy",
        "Промпроизводство EA, г/г",
        "eu",
        "industrial",
        "monthly",
        "eurostat",
        "sts_inpr_m/M.I15.Y.PROD.NS0030.EA20",
        "%",
    ),
    ("ru_ca_wb", "Сальдо текущего счёта % ВВП (WB)", "ru", "external", "annual", "world_bank", "BN.CAB.XOKA.GD.ZS/RU", "% GDP"),
    ("ru_debt_wb", "Госдолг % ВВП (WB)", "ru", "fiscal", "annual", "world_bank", "GC.DOD.TOTL.GD.ZS/RU", "% GDP"),
    ("us_trade_balance", "Trade balance, США", "us", "external", "monthly", "fred", "BOPGSTB", "USD bn"),
    ("us_ca_imf", "Current account % GDP, США", "us", "external", "annual", "imf", "BCA_NGDPD/USA", "% GDP"),
)

ENABLE_EXISTING: tuple[str, ...] = (
    "us_building_permits",
    "us_new_home_sales",
    "us_real_disposable_income",
    "us_financial_conditions",
    "us_pce_level",
    "us_retail_sales_yoy",
    "us_capacity_utilization",
    "us_business_inventories",
    "ru_fx_reserves",
    "ru_m2",
    "ru_ppi_yoy",
    "ru_food_cpi_yoy",
    "ru_services_cpi_yoy",
    "ru_investment_yoy",
    "eu_construction_yoy",
    "eu_retail_sales_yoy",
    "eu_industrial_new_orders",
    "eu_house_price_yoy",
    "de_industry_pct_gdp_wb",
    "moex_gold_futures",
    "moex_brent_futures",
    "world_exports_pct_gdp_wb",
    "world_imports_pct_gdp_wb",
    "world_fdi_pct_gdp_wb",
    "cn_exports_pct_gdp_wb",
    "tr_current_account_wb",
    "global_trade_volume_imf",
    "global_current_account_imf",
    "eu_gov_debt_pct_gdp",
    "eu_budget_balance_pct_gdp",
    "us_debt_imf",
    "cn_debt_imf",
    "jp_debt_imf",
    "de_debt_imf",
    "gb_debt_imf",
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

    enable_stmt = sa.text("UPDATE indicators SET enabled = true WHERE id = :id")
    for indicator_id in ENABLE_EXISTING:
        bind.execute(enable_stmt, {"id": indicator_id})


def downgrade() -> None:
    bind = op.get_bind()
    for id_, *_ in NEW_INDICATORS:
        bind.execute(sa.text("DELETE FROM indicators WHERE id = :id"), {"id": id_})
    disable_stmt = sa.text("UPDATE indicators SET enabled = false WHERE id = :id")
    for indicator_id in ENABLE_EXISTING:
        bind.execute(disable_stmt, {"id": indicator_id})
