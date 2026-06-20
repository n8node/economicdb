"""fix indicator external ids and eurostat/oecd/imf keys

Revision ID: 015
Revises: 014
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXTERNAL_ID_UPDATES: dict[str, str] = {
    "eu_ppi_yoy": "sts_inpp_m/M.PRC_PRR.B.NSA.PCH_SM.EA20",
    "eu_services_ppi_yoy": "sts_sepp_q/Q.PRC_PRR.H.NSA.PCH_SM.EA20",
    "eu_construction_yoy": "sts_copr_m/M.PRD.F.SCA.I21.EA20",
    "eu_house_price_yoy": "prc_hpi_q/Q.TOTAL.RCH_A.EA20",
    "eu_retail_sales_yoy": "sts_trtu_m/M.VOL_SLS.G.SCA.I21.EA20",
    "eu_employment_q_yoy": "namq_10_a10_e/Q.PCH_SM_PER.TOTAL.NSA.EMP_DC.EA20",
    "eu_budget_balance_pct_gdp": "gov_10q_ggnfa/Q.PC_GDP.NSA.S13.B9.EA20",
    "eu_building_permits_yoy": "sts_cobp_m/M.BPRM_SQM.CPA_F41001_41002.NSA.PCH_SM.EA20",
    "eu_industrial_production_yoy": "sts_inpr_m/M.PRD.B-D.SCA.I21.EA20",
    "oecd_cli_us": "CLI/USA.M.LI.IX._Z.AA.IX._Z.H",
    "oecd_cli_eu": "CLI/G4E.M.LI.IX._Z.AA.IX._Z.H",
    "oecd_cli_cn": "CLI/CHN.M.LI.IX._Z.AA.IX._Z.H",
    "oecd_cli_jp": "CLI/JPN.M.LI.IX._Z.AA.IX._Z.H",
    "oecd_cli_de": "CLI/DEU.M.LI.IX._Z.AA.IX._Z.H",
    "global_gdp_imf": "NGDP_RPCH/WEOWORLD",
    "global_cpi_imf": "PCPIPCH/WEOWORLD",
    "global_trade_volume_imf": "TM_RPCH/WEOWORLD",
    "global_current_account_imf": "BCA_NGDPD/WEOWORLD",
    "world_inflation_wb": "PCPIPCH/WEOWORLD",
    "us_lei": "USALOLITOONOSTSAM",
    "gold_spot": "GOLDPMGBD228NLBM",
    "ru_gdp_q_yoy": "fedstat:31077",
    "ru_mortgage_rate": "HTML:MortgageRateAverage",
    "eu_industrial_new_orders": "BTS/DEU.M.OI.PB.C.Y._Z.T.N",
    "oecd_cci_us": "UMCSENT",
    "oecd_cci_eu": "ei_bsco_m/M.BS-CSMCI.SA.BAL.EA20",
    "oecd_unemployment_g7": "LUR/MAE",
}

SOURCE_UPDATES: dict[str, tuple[str, str, str | None]] = {
    "eu_industrial_new_orders": ("oecd", "BTS/DEU.M.OI.PB.C.Y._Z.T.N", None),
    "oecd_real_gdp_g7": ("imf", "NGDP_RPCH/MAE", None),
    "world_inflation_wb": ("imf", "PCPIPCH/WEOWORLD", None),
    "oecd_cci_us": ("fred", "UMCSENT", None),
    "oecd_cci_eu": ("eurostat", "ei_bsco_m/M.BS-CSMCI.SA.BAL.EA20", None),
    "oecd_unemployment_g7": ("imf", "LUR/MAE", "annual"),
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
    for indicator_id, (source, external_id, frequency) in SOURCE_UPDATES.items():
        if frequency:
            op.execute(
                sa.text(
                    """
                    UPDATE indicators
                    SET source = :source, external_id = :external_id, frequency = :frequency
                    WHERE id = :indicator_id
                    """
                ).bindparams(
                    source=source,
                    external_id=external_id,
                    frequency=frequency,
                    indicator_id=indicator_id,
                )
            )
        else:
            op.execute(
                sa.text(
                    """
                    UPDATE indicators
                    SET source = :source, external_id = :external_id
                    WHERE id = :indicator_id
                    """
                ).bindparams(source=source, external_id=external_id, indicator_id=indicator_id)
            )


def downgrade() -> None:
    pass
