"""add world_bank and moex data providers

Revision ID: 008
Revises: 007
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO data_providers (id, name_ru, enabled, base_url)
            VALUES
                (
                    'world_bank',
                    'World Bank',
                    false,
                    'https://api.worldbank.org/v2'
                ),
                (
                    'moex',
                    'MOEX ISS',
                    false,
                    'https://iss.moex.com/iss'
                )
            ON CONFLICT (id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM data_providers WHERE id IN ('world_bank', 'moex')"))
