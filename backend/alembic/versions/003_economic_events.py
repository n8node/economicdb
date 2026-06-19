"""economic events

Revision ID: 003
Revises: 002
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "economic_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title_ru", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=8), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("importance", sa.String(length=8), nullable=False),
        sa.Column("scheduled_at_msk", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("forecast", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("previous", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("surprise", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("linked_indicator_id", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_economic_events_scheduled_at_msk", "economic_events", ["scheduled_at_msk"])
    op.create_index("ix_economic_events_country", "economic_events", ["country"])


def downgrade() -> None:
    op.drop_index("ix_economic_events_country", table_name="economic_events")
    op.drop_index("ix_economic_events_scheduled_at_msk", table_name="economic_events")
    op.drop_table("economic_events")
