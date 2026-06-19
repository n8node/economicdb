from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogTemplate:
    id: str
    name_ru: str
    country: str
    category: str
    frequency: str
    source: str
    external_id: str
    unit: str
    wave: str


CATALOG_TEMPLATES: list[CatalogTemplate] = [
    CatalogTemplate("eur_rub", "EUR / RUB", "ru", "fx", "daily", "cbr", "R01239", "RUB", "w1"),
    CatalogTemplate("us_core_cpi_yoy", "Core CPI, г/г", "us", "inflation", "monthly", "fred", "CPILFESL", "%", "w1"),
    CatalogTemplate("us_10y_yield", "10Y Treasury yield", "us", "rates", "daily", "fred", "DGS10", "%", "w1"),
    CatalogTemplate("us_unemployment", "Unemployment rate", "us", "labor", "monthly", "fred", "UNRATE", "%", "w1"),
    CatalogTemplate("us_indpro_yoy", "Industrial production", "us", "industrial", "monthly", "fred", "INDPRO", "index", "w1"),
    CatalogTemplate("sp500", "S&P 500", "us", "equities", "daily", "fred", "SP500", "index", "w1"),
    CatalogTemplate("ecb_mro_rate", "ECB Main Refinancing Rate", "eu", "rates", "monthly", "ecb", "FM/D.U2.EUR.4F.KR.MRR_FR.LEV", "%", "w1"),
    CatalogTemplate("moex_rtsi", "Индекс RTS", "ru", "equities", "daily", "moex", "stock/index/RTSI/CLOSE", "index", "w1"),
    CatalogTemplate("moex_rgbi", "Индекс гособлигаций RGBI", "ru", "rates", "daily", "moex", "stock/index/RGBI/CLOSE", "index", "w1"),
    CatalogTemplate("cn_gdp_wb", "GDP growth (WB)", "cn", "gdp", "annual", "world_bank", "NY.GDP.MKTP.KD.ZG/CN", "%", "w1"),
    CatalogTemplate("ru_retail_yoy", "Розничная торговля, г/г", "ru", "consumption", "monthly", "rosstat", "fedstat:42934", "%", "w1"),
    CatalogTemplate("ru_unemployment", "Безработица", "ru", "labor", "monthly", "rosstat", "fedstat:57614", "%", "w1"),
    CatalogTemplate("ru_gdp_q_yoy", "ВВП, г/г", "ru", "gdp", "quarterly", "rosstat", "fedstat:57746", "%", "w1"),
    CatalogTemplate("us_pce_yoy", "PCE, г/г", "us", "inflation", "monthly", "fred", "PCEPI", "%", "w2"),
    CatalogTemplate("us_retail_sales", "Retail sales", "us", "consumption", "monthly", "fred", "RSXFS", "index", "w2"),
    CatalogTemplate("eu_unemployment", "Unemployment rate", "eu", "labor", "monthly", "eurostat", "ei_lmhr_m/M.PC_ACT.SA.LM-UN-T-TOT.EA21", "%", "w2"),
    CatalogTemplate("eu_gdp_q_yoy", "GDP, г/г", "eu", "gdp", "quarterly", "eurostat", "namq_10_gdp/Q.CLV_PCH_PRE.SCA.B1GQ.EA20", "%", "w2"),
    CatalogTemplate("jp_gdp_yoy_wb", "GDP growth (WB)", "jp", "gdp", "annual", "world_bank", "NY.GDP.MKTP.KD.ZG/JP", "%", "w2"),
    CatalogTemplate("de_hicp_yoy", "HICP Germany, г/г", "eu", "inflation", "monthly", "eurostat", "PRC_HICP_MANR/M.RCH_A.CP00.DE", "%", "w2"),
    CatalogTemplate("oil_wti", "WTI crude", "world", "commodities", "daily", "fred", "DCOILWTICO", "USD/bbl", "w2"),
]

WAVES = ("w1", "w2", "w3", "w4", "w5", "all")


def templates_for_wave(wave: str) -> list[CatalogTemplate]:
    if wave == "all":
        return list(CATALOG_TEMPLATES)
    return [item for item in CATALOG_TEMPLATES if item.wave == wave]
