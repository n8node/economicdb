from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.indicators import Indicator

logger = structlog.get_logger()


@dataclass(frozen=True)
class RealIndicatorSeed:
    id: str
    name_ru: str
    country: str
    category: str
    frequency: str
    source: str
    external_id: str
    unit: str


REAL_INDICATORS: list[RealIndicatorSeed] = [
    RealIndicatorSeed("cbr_key_rate", "Ключевая ставка ЦБ", "ru", "rates", "monthly", "cbr", "KeyRate", "%"),
    RealIndicatorSeed("usd_rub", "USD / RUB", "ru", "fx", "daily", "cbr", "R01235", "RUB"),
    RealIndicatorSeed("ru_cpi_yoy", "ИПЦ России, г/г", "ru", "inflation", "monthly", "rosstat", "fedstat:31074", "%"),
    RealIndicatorSeed(
        "ru_industrial_yoy",
        "Промышленное производство, г/г",
        "ru",
        "industrial",
        "monthly",
        "rosstat",
        "fedstat:57806",
        "%",
    ),
    RealIndicatorSeed(
        "eu_hicp_yoy",
        "HICP EU, г/г",
        "eu",
        "inflation",
        "monthly",
        "oecd",
        "EA20.M.HICP.CPI.PA._T.N.GY",
        "%",
    ),
    RealIndicatorSeed(
        "eu_hicp_yoy_eurostat",
        "HICP EU, г/г (Eurostat)",
        "eu",
        "inflation",
        "monthly",
        "eurostat",
        "PRC_HICP_MANR/M.RCH_A.CP00.EA20",
        "%",
    ),
    RealIndicatorSeed(
        "ecb_deposit_rate",
        "ECB Deposit Facility Rate",
        "eu",
        "rates",
        "monthly",
        "ecb",
        "FM/D.U2.EUR.4F.KR.DFR.LEV",
        "%",
    ),
    RealIndicatorSeed("fed_funds", "Fed Funds Rate", "us", "rates", "monthly", "fred", "FEDFUNDS", "%"),
    RealIndicatorSeed("us_cpi_yoy", "US CPI, г/г", "us", "inflation", "monthly", "fred", "CPIAUCSL", "%"),
    RealIndicatorSeed("us_nfp", "Nonfarm Payrolls, США", "us", "labor", "monthly", "fred", "PAYEMS", "тыс."),
    RealIndicatorSeed("us_gdp_yoy", "ВВП США, г/г", "us", "gdp", "quarterly", "fred", "A191RL1Q225SBEA", "%"),
    RealIndicatorSeed(
        "cn_gdp_yoy",
        "ВВП Китая, real YoY",
        "cn",
        "gdp",
        "annual",
        "imf",
        "NGDP_RPCH/CHN",
        "%",
    ),
    RealIndicatorSeed(
        "ru_gdp_yoy_wb",
        "ВВП России, рост",
        "ru",
        "gdp",
        "annual",
        "world_bank",
        "NY.GDP.MKTP.KD.ZG/RU",
        "%",
    ),
    RealIndicatorSeed(
        "imoex",
        "Индекс MOEX",
        "ru",
        "equities",
        "daily",
        "moex",
        "stock/index/IMOEX/CLOSE",
        "index",
    ),
    RealIndicatorSeed("oil_brent", "Нефть Brent", "world", "commodities", "daily", "fred", "DCOILBRENTEU", "USD"),
]


async def seed_real_indicators(session: AsyncSession) -> None:
    now = datetime.now(timezone.utc)
    created = 0
    updated = 0
    for seed in REAL_INDICATORS:
        row = await session.get(Indicator, seed.id)
        if row is None:
            session.add(
                Indicator(
                    id=seed.id,
                    name_ru=seed.name_ru,
                    country=seed.country,
                    category=seed.category,
                    frequency=seed.frequency,
                    source=seed.source,
                    external_id=seed.external_id,
                    unit=seed.unit,
                    last_value=None,
                    last_change=None,
                    updated_at=now,
                )
            )
            created += 1
        else:
            row.name_ru = seed.name_ru
            row.country = seed.country
            row.category = seed.category
            row.frequency = seed.frequency
            row.source = seed.source
            row.external_id = seed.external_id
            row.unit = seed.unit
            updated += 1

    await session.commit()
    logger.info("real_indicator_catalog_seed_complete", created=created, updated=updated)


REAL_INDICATOR_IDS = {seed.id for seed in REAL_INDICATORS}
