"""indicators and data providers

Revision ID: 002
Revises: 001
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "indicators",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name_ru", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=8), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("frequency", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("last_value", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("last_change", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "indicator_values",
        sa.Column("indicator_id", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.PrimaryKeyConstraint("indicator_id", "observed_at"),
    )
    op.create_table(
        "data_providers",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name_ru", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("credentials_encrypted", sa.Text(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(length=32), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.bulk_insert(
        sa.table(
            "data_providers",
            sa.column("id", sa.String),
            sa.column("name_ru", sa.String),
            sa.column("enabled", sa.Boolean),
        ),
        [
            {"id": "cbr", "name_ru": "Банк России", "enabled": False},
            {"id": "rosstat", "name_ru": "Росстат", "enabled": False},
            {"id": "fred", "name_ru": "FRED", "enabled": False},
            {"id": "oecd", "name_ru": "OECD", "enabled": False},
        ],
    )


def downgrade() -> None:
    op.drop_table("data_providers")
    op.drop_table("indicator_values")
    op.drop_table("indicators")
