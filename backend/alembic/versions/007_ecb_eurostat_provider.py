"""add ecb_eurostat data provider

Revision ID: 007
Revises: 006
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO data_providers (id, name_ru, enabled, base_url)
            VALUES (
                'ecb_eurostat',
                'ECB / Eurostat',
                false,
                'https://data-api.ecb.europa.eu/service/data'
            )
            ON CONFLICT (id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM data_providers WHERE id = 'ecb_eurostat'"))
