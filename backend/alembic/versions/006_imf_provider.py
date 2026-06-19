"""add imf data provider

Revision ID: 006
Revises: 005
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO data_providers (id, name_ru, enabled, base_url)
            VALUES (
                'imf',
                'IMF',
                false,
                'https://www.imf.org/external/datamapper/api/v1'
            )
            ON CONFLICT (id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM data_providers WHERE id = 'imf'"))
