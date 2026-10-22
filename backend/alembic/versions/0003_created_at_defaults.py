"""Add the server default for created_at that migration 0001 omitted.

Revision ID: 0003_created_at_defaults
Revises: 0002_complete_item_bank_schema
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_created_at_defaults"
down_revision = "0002_complete_item_bank_schema"
branch_labels = None
depends_on = None

TABLES = ("users", "courses", "topics")


def upgrade() -> None:
    for table in TABLES:
        op.alter_column(table, "created_at", server_default=sa.text("now()"))


def downgrade() -> None:
    for table in TABLES:
        op.alter_column(table, "created_at", server_default=None)
