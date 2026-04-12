"""Add direct_memberships and effective_memberships tables.

Revision ID: 003
Revises: 002
Create Date: 2026-04-11
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "direct_memberships",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("directory_id", sa.Uuid(), sa.ForeignKey("directories.id"), nullable=False),
        sa.Column("parent_dn", sa.String(), nullable=False),
        sa.Column("child_dn", sa.String(), nullable=False),
        sa.Column(
            "child_type",
            sa.Enum("USER", "GROUP", name="childtype"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("directory_id", "parent_dn", "child_dn", name="uq_direct_membership"),
    )
    op.create_index("ix_direct_memberships_directory_id", "direct_memberships", ["directory_id"])
    op.create_index("ix_direct_memberships_parent_dn", "direct_memberships", ["directory_id", "parent_dn"])
    op.create_index("ix_direct_memberships_child_dn", "direct_memberships", ["directory_id", "child_dn"])

    op.create_table(
        "effective_memberships",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("directory_id", sa.Uuid(), sa.ForeignKey("directories.id"), nullable=False),
        sa.Column("user_dn", sa.String(), nullable=False),
        sa.Column("group_dn", sa.String(), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("path", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_effective_memberships_directory_id", "effective_memberships", ["directory_id"])
    op.create_index("ix_effective_memberships_user", "effective_memberships", ["directory_id", "user_dn"])
    op.create_index("ix_effective_memberships_group", "effective_memberships", ["directory_id", "group_dn"])


def downgrade() -> None:
    op.drop_table("effective_memberships")
    op.drop_table("direct_memberships")
    sa.Enum(name="childtype").drop(op.get_bind(), checkfirst=True)
