"""provider test status

Revision ID: 005
Revises: 004
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("data_providers", sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("data_providers", sa.Column("last_test_status", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("data_providers", "last_test_status")
    op.drop_column("data_providers", "last_test_at")
