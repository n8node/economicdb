"""fix rosstat fedstat external ids

Revision ID: 011
Revises: 010
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE indicators
            SET external_id = 'fedstat:31066'
            WHERE id = 'ru_retail_yoy'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators
            SET external_id = 'fedstat:43062', frequency = 'quarterly'
            WHERE id = 'ru_unemployment'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE indicators
            SET external_id = 'fedstat:42934'
            WHERE id = 'ru_retail_yoy'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE indicators
            SET external_id = 'fedstat:57614', frequency = 'monthly'
            WHERE id = 'ru_unemployment'
            """
        )
    )
