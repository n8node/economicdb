"""add indicators.enabled and fix eurostat external ids

Revision ID: 010
Revises: 009
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "indicators",
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators
            SET external_id = 'ei_lmhr_m/M.PC_ACT.SA.LM-UN-T-TOT.EA21'
            WHERE id = 'eu_unemployment'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators
            SET external_id = 'namq_10_gdp/Q.CLV_PCH_PRE.SCA.B1GQ.EA20'
            WHERE id = 'eu_gdp_q_yoy'
            """
        )
    )


def downgrade() -> None:
    op.drop_column("indicators", "enabled")
