"""add etl_jobs table

Revision ID: 009
Revises: 008
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "etl_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider_id", sa.String(length=32), nullable=False),
        sa.Column("trigger", sa.String(length=16), nullable=False, server_default="manual"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="running"),
        sa.Column("country", sa.String(length=8), nullable=True),
        sa.Column("indicator_ids", sa.Text(), nullable=True),
        sa.Column("date_from", sa.Date(), nullable=True),
        sa.Column("date_to", sa.Date(), nullable=True),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("records", sa.Integer(), nullable=True),
        sa.Column("synced_indicators", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("admin_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_etl_jobs_provider_started", "etl_jobs", ["provider_id", "started_at"])


def downgrade() -> None:
    op.drop_index("ix_etl_jobs_provider_started", table_name="etl_jobs")
    op.drop_table("etl_jobs")
