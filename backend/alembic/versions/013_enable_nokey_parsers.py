"""fix parser external ids for cbr rosstat oecd

Revision ID: 013
Revises: 012
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXTERNAL_ID_UPDATES: dict[str, str] = {
    "ru_ppi_yoy": "fedstat:57609",
    "ru_food_cpi_yoy": "fedstat:31074/food",
    "ru_services_cpi_yoy": "fedstat:31074/services",
    "ru_investment_yoy": "fedstat:31081",
    "oecd_cli_us": "CLI/USA.M.LI...AA...H",
    "oecd_cli_eu": "CLI/G4E.M.LI...AA...H",
    "oecd_cli_cn": "CLI/CHN.M.LI...AA...H",
    "oecd_cli_jp": "CLI/JPN.M.LI...AA...H",
    "oecd_cli_de": "CLI/DEU.M.LI...AA...H",
    "oecd_bci_us": "BTS/USA.M.BCICP.PB.C.Y._Z._Z.N",
    "oecd_bci_eu": "BTS/EA20.M.BCICP.PB.C.Y._Z._Z.N",
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


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE indicators SET external_id = 'fedstat:TODO_PPI' WHERE id = 'ru_ppi_yoy'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators SET external_id = 'fedstat:TODO_FOOD_CPI' WHERE id = 'ru_food_cpi_yoy'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators SET external_id = 'fedstat:TODO_SERVICES_CPI' WHERE id = 'ru_services_cpi_yoy'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators SET external_id = 'fedstat:TODO_INVESTMENT' WHERE id = 'ru_investment_yoy'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators SET external_id = 'USA.M.LI...' WHERE id = 'oecd_cli_us'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators SET external_id = 'EA20.M.LI...' WHERE id = 'oecd_cli_eu'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators SET external_id = 'CHN.M.LI...' WHERE id = 'oecd_cli_cn'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators SET external_id = 'JPN.M.LI...' WHERE id = 'oecd_cli_jp'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators SET external_id = 'DEU.M.LI...' WHERE id = 'oecd_cli_de'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators SET external_id = 'USA.M.BCI...' WHERE id = 'oecd_bci_us'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators SET external_id = 'EA20.M.BCI...' WHERE id = 'oecd_bci_eu'
            """
        )
    )
