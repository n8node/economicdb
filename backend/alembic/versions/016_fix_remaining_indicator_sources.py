"""fix remaining indicator external ids and sources

Revision ID: 016
Revises: 015
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXTERNAL_ID_UPDATES: dict[str, str] = {
    "ru_food_cpi_yoy": "fedstat:31074/food",
    "ru_services_cpi_yoy": "fedstat:31074/services",
    "ru_mortgage_rate": "HTML:MortgageRateAverage",
    "gold_spot": "GOLDPMGBD228NLBM",
    "eu_building_permits_yoy": "sts_cobp_m/M.BPRM_SQM.CPA_F41001_41002.NSA.PCH_SM.EA20",
    "eu_construction_yoy": "sts_copr_m/M.PRD.F.SCA.I21.EA20",
    "eu_retail_sales_yoy": "sts_trtu_m/M.VOL_SLS.G.SCA.I21.EA20",
    "us_lei": "USALOLITOONOSTSAM",
}

SOURCE_UPDATES: dict[str, tuple[str, str, str | None, str | None]] = {
    "ru_gdp_q_yoy": ("imf", "NGDP_RPCH/RUS", "annual", "ВВП, г/г (IMF)"),
    "ru_investment_yoy": ("world_bank", "NE.GDI.TOTL.KD.ZG/RU", "annual", "Валовое накопление, г/г (WB)"),
    "global_trade_volume_imf": (
        "world_bank",
        "NE.EXP.GNFS.KD.ZG/WLD",
        "annual",
        "World exports growth",
    ),
}


def upgrade() -> None:
    for indicator_id, external_id in EXTERNAL_ID_UPDATES.items():
        op.execute(
            sa.text(
                """
                UPDATE indicators
                SET external_id = :external_id
                WHERE id = :indicator_id
                """
            ).bindparams(external_id=external_id, indicator_id=indicator_id)
        )

    for indicator_id, (source, external_id, frequency, name_ru) in SOURCE_UPDATES.items():
        op.execute(
            sa.text(
                """
                UPDATE indicators
                SET source = :source,
                    external_id = :external_id,
                    frequency = :frequency,
                    name_ru = :name_ru
                WHERE id = :indicator_id
                """
            ).bindparams(
                source=source,
                external_id=external_id,
                frequency=frequency,
                name_ru=name_ru,
                indicator_id=indicator_id,
            )
        )


def downgrade() -> None:
    pass
