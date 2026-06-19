"""add multisource indicator catalog package

Revision ID: 012
Revises: 011
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDICATORS: tuple[tuple[str, str, str, str, str, str, str, str], ...] = (
    ("jpy_rub", "JPY / RUB", "ru", "fx", "daily", "cbr", "R01820", "RUB"),
    ("chf_rub", "CHF / RUB", "ru", "fx", "daily", "cbr", "R01775", "RUB"),
    ("try_rub", "TRY / RUB", "ru", "fx", "daily", "cbr", "R01700J", "RUB"),
    ("kzt_rub", "KZT / RUB", "ru", "fx", "daily", "cbr", "R01335", "RUB"),
    ("byn_rub", "BYN / RUB", "ru", "fx", "daily", "cbr", "R01090B", "RUB"),
    ("ru_fx_reserves", "Международные резервы РФ", "ru", "external", "monthly", "cbr", "SOAP:InternationalReserves", "USD bn"),
    ("ru_m2", "Денежная масса M2", "ru", "rates", "monthly", "cbr", "SOAP:MoneySupply/M2", "RUB bn"),
    ("ru_mortgage_rate", "Средняя ставка по ипотеке", "ru", "rates", "monthly", "cbr", "SOAP:MortgageRate", "%"),
    ("us_retail_sales_yoy", "Retail sales, г/г", "us", "consumption", "monthly", "fred", "RSXFS", "%"),
    ("us_jolts_openings", "JOLTS job openings", "us", "labor", "monthly", "fred", "JTSJOL", "thousand"),
    ("us_building_permits", "Building permits", "us", "construction", "monthly", "fred", "PERMIT", "thousand"),
    ("us_new_home_sales", "New home sales", "us", "construction", "monthly", "fred", "HSN1F", "thousand"),
    ("us_capacity_utilization", "Capacity utilization", "us", "industrial", "monthly", "fred", "TCU", "%"),
    ("us_pce_level", "Personal consumption expenditures", "us", "consumption", "monthly", "fred", "PCE", "USD bn"),
    ("us_real_disposable_income", "Real disposable personal income", "us", "income", "monthly", "fred", "DSPIC96", "USD bn"),
    ("us_business_inventories", "Business inventories", "us", "industrial", "monthly", "fred", "BUSINV", "USD mn"),
    ("us_5y_breakeven", "5Y inflation expectations", "us", "rates", "daily", "fred", "T5YIE", "%"),
    ("us_10y_breakeven", "10Y inflation expectations", "us", "rates", "daily", "fred", "T10YIE", "%"),
    ("us_high_yield_spread", "HY credit spread", "us", "rates", "daily", "fred", "BAMLH0A0HYM2", "%"),
    ("us_financial_conditions", "Chicago Fed NFCI", "us", "financial", "weekly", "fred", "NFCI", "index"),
    ("nasdaq", "NASDAQ Composite", "us", "equities", "daily", "fred", "NASDAQCOM", "index"),
    ("vix", "VIX volatility", "us", "equities", "daily", "fred", "VIXCLS", "index"),
    ("ecb_eur_gbp", "EUR / GBP", "eu", "fx", "daily", "ecb", "EXR/D.GBP.EUR.SP00.A", "rate"),
    ("ecb_eur_jpy", "EUR / JPY", "eu", "fx", "daily", "ecb", "EXR/D.JPY.EUR.SP00.A", "rate"),
    ("ecb_eur_chf", "EUR / CHF", "eu", "fx", "daily", "ecb", "EXR/D.CHF.EUR.SP00.A", "rate"),
    ("ecb_eur_cny", "EUR / CNY", "eu", "fx", "daily", "ecb", "EXR/D.CNY.EUR.SP00.A", "rate"),
    ("ecb_eur_rub", "EUR / RUB (ECB)", "eu", "fx", "daily", "ecb", "EXR/D.RUB.EUR.SP00.A", "rate"),
    ("ecb_3m_money_market", "Euro area 3M money market rate", "eu", "rates", "monthly", "ecb", "FM/M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA", "%"),
    ("ecb_bank_lending_households", "Lending to households", "eu", "credit", "monthly", "ecb", "BSI/M.U2.N.A.A20.A.1.U2.2250.Z01.E", "EUR mn"),
    ("ecb_bank_lending_corporates", "Lending to non-financial corporates", "eu", "credit", "monthly", "ecb", "BSI/M.U2.N.A.A20.A.1.U2.2240.Z01.E", "EUR mn"),
    ("moex_oilgas", "Индекс нефти и газа", "ru", "equities", "daily", "moex", "stock/index/MOEXOG/CLOSE", "index"),
    ("moex_financials", "Индекс финансов", "ru", "equities", "daily", "moex", "stock/index/MOEXFN/CLOSE", "index"),
    ("moex_metals", "Индекс металлов и добычи", "ru", "equities", "daily", "moex", "stock/index/MOEXMM/CLOSE", "index"),
    ("moex_consumer", "Индекс потребительского сектора", "ru", "equities", "daily", "moex", "stock/index/MOEXCN/CLOSE", "index"),
    ("moex_it", "Индекс IT", "ru", "equities", "daily", "moex", "stock/index/MOEXIT/CLOSE", "index"),
    ("moex_transport", "Индекс транспорта", "ru", "equities", "daily", "moex", "stock/index/MOEXTN/CLOSE", "index"),
    ("moex_usd_tom", "USD/RUB TOM (MOEX)", "ru", "fx", "daily", "moex", "currency/selt/USD000UTSTOM/CLOSE", "RUB"),
    ("moex_eur_tom", "EUR/RUB TOM (MOEX)", "ru", "fx", "daily", "moex", "currency/selt/EUR_RUB__TOM/CLOSE", "RUB"),
    ("moex_cny_tom", "CNY/RUB TOM (MOEX)", "ru", "fx", "daily", "moex", "currency/selt/CNYRUB_TOM/CLOSE", "RUB"),
    ("moex_gold_futures", "Фьючерс на золото", "ru", "commodities", "daily", "moex", "futures/forts/GOLD/CLOSE", "RUB"),
    ("moex_brent_futures", "Фьючерс Brent", "ru", "commodities", "daily", "moex", "futures/forts/BR/CLOSE", "USD/bbl"),
    ("ru_ppi_yoy", "Индекс цен производителей, г/г", "ru", "inflation", "monthly", "rosstat", "fedstat:TODO_PPI", "%"),
    ("ru_food_cpi_yoy", "Продовольственная инфляция, г/г", "ru", "inflation", "monthly", "rosstat", "fedstat:TODO_FOOD_CPI", "%"),
    ("ru_services_cpi_yoy", "Инфляция услуг, г/г", "ru", "inflation", "monthly", "rosstat", "fedstat:TODO_SERVICES_CPI", "%"),
    ("ru_construction_yoy", "Объём строительных работ, г/г", "ru", "construction", "monthly", "rosstat", "fedstat:TODO_CONSTRUCTION", "%"),
    ("ru_real_wages_yoy", "Реальная зарплата, г/г", "ru", "labor", "monthly", "rosstat", "fedstat:TODO_REAL_WAGES", "%"),
    ("ru_real_income_yoy", "Реальные располагаемые доходы, г/г", "ru", "income", "quarterly", "rosstat", "fedstat:TODO_REAL_INCOME", "%"),
    ("ru_investment_yoy", "Инвестиции в основной капитал, г/г", "ru", "investment", "quarterly", "rosstat", "fedstat:TODO_INVESTMENT", "%"),
    ("ru_freight_turnover_yoy", "Грузооборот транспорта, г/г", "ru", "transport", "monthly", "rosstat", "fedstat:TODO_FREIGHT_TURNOVER", "%"),
    ("ru_agriculture_yoy", "Сельхозпроизводство, г/г", "ru", "agriculture", "monthly", "rosstat", "fedstat:TODO_AGRICULTURE", "%"),
    ("ru_exports_goods", "Экспорт товаров", "ru", "external", "monthly", "rosstat", "fedstat:TODO_EXPORTS_GOODS", "USD mn"),
    ("ru_imports_goods", "Импорт товаров", "ru", "external", "monthly", "rosstat", "fedstat:TODO_IMPORTS_GOODS", "USD mn"),
    ("eu_core_hicp_yoy", "Core HICP, г/г", "eu", "inflation", "monthly", "eurostat", "PRC_HICP_MANR/M.RCH_A.TOT_X_NRG_FOOD.EA20", "%"),
    ("eu_food_hicp_yoy", "Food HICP, г/г", "eu", "inflation", "monthly", "eurostat", "PRC_HICP_MANR/M.RCH_A.CP01.EA20", "%"),
    ("eu_energy_hicp_yoy", "Energy HICP, г/г", "eu", "inflation", "monthly", "eurostat", "PRC_HICP_MANR/M.RCH_A.NRG.EA20", "%"),
    ("eu_ppi_yoy", "Producer prices, г/г", "eu", "inflation", "monthly", "eurostat", "sts_inpp_m/M.I15.Y.PROD.NS0030.EA20", "%"),
    ("eu_services_ppi_yoy", "Services producer prices", "eu", "inflation", "quarterly", "eurostat", "sts_sepp_q/Q.I15.Y.SERV.NS0030.EA20", "%"),
    ("eu_construction_yoy", "Construction output, г/г", "eu", "construction", "monthly", "eurostat", "sts_copr_m/M.I15.Y.CST.NS0030.EA20", "%"),
    ("eu_house_price_yoy", "House price index, г/г", "eu", "housing", "quarterly", "eurostat", "prc_hpi_q/Q.I15.Y.DW.EA20", "%"),
    ("eu_retail_sales_yoy", "Retail trade volume, г/г", "eu", "consumption", "monthly", "eurostat", "sts_trtu_m/M.I15.Y.RT.NS0030.EA20", "%"),
    ("eu_industrial_new_orders", "Industrial new orders", "eu", "industrial", "monthly", "eurostat", "sts_inno_m/M.I15.Y.TOTAL.NS0030.EA20", "%"),
    ("eu_employment_q_yoy", "Employment, г/г", "eu", "labor", "quarterly", "eurostat", "namq_10_a10_e/Q.PCH_SM_PER.TOTAL.EMP_DC.TOTAL.EA20", "%"),
    ("eu_gov_debt_pct_gdp", "Government debt % GDP", "eu", "fiscal", "quarterly", "eurostat", "gov_10q_ggdebt/Q.GD.S13.PC_GDP.EA20", "% GDP"),
    ("eu_budget_balance_pct_gdp", "Budget balance % GDP", "eu", "fiscal", "quarterly", "eurostat", "gov_10q_ggnfa/Q.NSA.B9.PC_GDP.S13.EA20", "% GDP"),
    ("oecd_cli_us", "OECD CLI USA", "us", "leading", "monthly", "oecd", "USA.M.LI...", "index"),
    ("oecd_cli_eu", "OECD CLI Euro Area", "eu", "leading", "monthly", "oecd", "EA20.M.LI...", "index"),
    ("oecd_cli_cn", "OECD CLI China", "cn", "leading", "monthly", "oecd", "CHN.M.LI...", "index"),
    ("oecd_cli_jp", "OECD CLI Japan", "jp", "leading", "monthly", "oecd", "JPN.M.LI...", "index"),
    ("oecd_cli_de", "OECD CLI Germany", "de", "leading", "monthly", "oecd", "DEU.M.LI...", "index"),
    ("oecd_bci_us", "Business confidence USA", "us", "sentiment", "monthly", "oecd", "USA.M.BCI...", "index"),
    ("oecd_bci_eu", "Business confidence Euro Area", "eu", "sentiment", "monthly", "oecd", "EA20.M.BCI...", "index"),
    ("oecd_cci_us", "Consumer confidence USA", "us", "sentiment", "monthly", "oecd", "USA.M.CCI...", "index"),
    ("oecd_cci_eu", "Consumer confidence Euro Area", "eu", "sentiment", "monthly", "oecd", "EA20.M.CCI...", "index"),
    ("oecd_real_gdp_g7", "Real GDP G7", "world", "gdp", "quarterly", "oecd", "G7.Q.GDP...", "index"),
    ("oecd_unemployment_g7", "Unemployment G7", "world", "labor", "monthly", "oecd", "G7.M.UNEMP...", "%"),
    ("world_gdp_growth_wb", "World GDP growth", "world", "gdp", "annual", "world_bank", "NY.GDP.MKTP.KD.ZG/WLD", "%"),
    ("world_inflation_wb", "World inflation", "world", "inflation", "annual", "world_bank", "FP.CPI.TOTL.ZG/WLD", "%"),
    ("world_exports_pct_gdp_wb", "World exports % GDP", "world", "external", "annual", "world_bank", "NE.EXP.GNFS.ZS/WLD", "% GDP"),
    ("world_imports_pct_gdp_wb", "World imports % GDP", "world", "external", "annual", "world_bank", "NE.IMP.GNFS.ZS/WLD", "% GDP"),
    ("world_fdi_pct_gdp_wb", "World FDI inflows % GDP", "world", "external", "annual", "world_bank", "BX.KLT.DINV.WD.GD.ZS/WLD", "% GDP"),
    ("de_industry_pct_gdp_wb", "Germany industry % GDP", "de", "industrial", "annual", "world_bank", "NV.IND.TOTL.ZS/DE", "% GDP"),
    ("cn_exports_pct_gdp_wb", "China exports % GDP", "cn", "external", "annual", "world_bank", "NE.EXP.GNFS.ZS/CN", "% GDP"),
    ("in_inflation_wb", "India inflation", "in", "inflation", "annual", "world_bank", "FP.CPI.TOTL.ZG/IN", "%"),
    ("br_unemp_wb", "Brazil unemployment", "br", "labor", "annual", "world_bank", "SL.UEM.TOTL.ZS/BR", "%"),
    ("tr_current_account_wb", "Turkey current account % GDP", "tr", "external", "annual", "world_bank", "BN.CAB.XOKA.GD.ZS/TR", "% GDP"),
    ("global_gdp_imf", "World GDP growth (IMF)", "world", "gdp", "annual", "imf", "NGDP_RPCH/WLD", "%"),
    ("global_cpi_imf", "World inflation (IMF)", "world", "inflation", "annual", "imf", "PCPIPCH/WLD", "%"),
    ("global_trade_volume_imf", "World trade volume", "world", "external", "annual", "imf", "TM_RPCH/WLD", "%"),
    ("global_current_account_imf", "Global current account balance", "world", "external", "annual", "imf", "BCA_NGDPD/WLD", "% GDP"),
    ("us_debt_imf", "US govt debt % GDP", "us", "fiscal", "annual", "imf", "GGXWDG_NGDP/USA", "% GDP"),
    ("cn_debt_imf", "China govt debt % GDP", "cn", "fiscal", "annual", "imf", "GGXWDG_NGDP/CHN", "% GDP"),
    ("jp_debt_imf", "Japan govt debt % GDP", "jp", "fiscal", "annual", "imf", "GGXWDG_NGDP/JPN", "% GDP"),
    ("de_debt_imf", "Germany govt debt % GDP", "de", "fiscal", "annual", "imf", "GGXWDG_NGDP/DEU", "% GDP"),
    ("gb_debt_imf", "UK govt debt % GDP", "gb", "fiscal", "annual", "imf", "GGXWDG_NGDP/GBR", "% GDP"),
    ("in_gdp_imf", "India GDP growth", "in", "gdp", "annual", "imf", "NGDP_RPCH/IND", "%"),
    ("br_gdp_imf", "Brazil GDP growth", "br", "gdp", "annual", "imf", "NGDP_RPCH/BRA", "%"),
    ("tr_cpi_imf", "Turkey inflation", "tr", "inflation", "annual", "imf", "PCPIPCH/TUR", "%"),
)


def upgrade() -> None:
    bind = op.get_bind()
    stmt = sa.text(
        """
        INSERT INTO indicators (
            id, name_ru, country, category, frequency, source, external_id, unit, enabled
        )
        VALUES (
            :id, :name_ru, :country, :category, :frequency, :source, :external_id, :unit, false
        )
        ON CONFLICT (id) DO NOTHING
        """
    )
    for id_, name_ru, country, category, frequency, source, external_id, unit in INDICATORS:
        bind.execute(
            stmt,
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
    bind = op.get_bind()
    stmt = sa.text("DELETE FROM indicators WHERE id = :id")
    for id_, *_ in INDICATORS:
        bind.execute(stmt, {"id": id_})
