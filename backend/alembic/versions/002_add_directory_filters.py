"""Add user_filter and group_filter columns to directories.

Revision ID: 002
Revises: 001
Create Date: 2026-04-11
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

AD_USER_FILTER = "(objectClass=user)"
AD_GROUP_FILTER = "(objectClass=group)"


def upgrade() -> None:
    op.add_column(
        "directories",
        sa.Column(
            "user_filter",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default=AD_USER_FILTER,
        ),
    )
    op.add_column(
        "directories",
        sa.Column(
            "group_filter",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default=AD_GROUP_FILTER,
        ),
    )


def downgrade() -> None:
    op.drop_column("directories", "group_filter")
    op.drop_column("directories", "user_filter")
