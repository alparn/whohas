"""Add guid and stale columns to directory_users and directory_groups.

Revision ID: 004
Revises: 003
Create Date: 2026-04-13
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("directory_users", sa.Column("guid", sa.String(), nullable=True))
    op.add_column(
        "directory_users",
        sa.Column("stale", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_unique_constraint(
        "uq_directory_users_directory_id_guid",
        "directory_users",
        ["directory_id", "guid"],
    )
    op.create_index(
        "ix_directory_users_guid",
        "directory_users",
        ["directory_id", "guid"],
    )

    op.add_column("directory_groups", sa.Column("guid", sa.String(), nullable=True))
    op.add_column(
        "directory_groups",
        sa.Column("stale", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_unique_constraint(
        "uq_directory_groups_directory_id_guid",
        "directory_groups",
        ["directory_id", "guid"],
    )
    op.create_index(
        "ix_directory_groups_guid",
        "directory_groups",
        ["directory_id", "guid"],
    )


def downgrade() -> None:
    op.drop_index("ix_directory_groups_guid", table_name="directory_groups")
    op.drop_constraint("uq_directory_groups_directory_id_guid", "directory_groups", type_="unique")
    op.drop_column("directory_groups", "stale")
    op.drop_column("directory_groups", "guid")

    op.drop_index("ix_directory_users_guid", table_name="directory_users")
    op.drop_constraint("uq_directory_users_directory_id_guid", "directory_users", type_="unique")
    op.drop_column("directory_users", "stale")
    op.drop_column("directory_users", "guid")
