"""Initial schema — directories, users, groups, sync_runs.

Revision ID: 001
Revises: None
Create Date: 2026-04-11
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "directories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("host", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False, server_default="389"),
        sa.Column("use_ssl", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("bind_dn", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("bind_password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("base_dn", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("last_full_sync_at", sa.DateTime(), nullable=True),
        sa.Column("last_usn", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_directories_name", "directories", ["name"])

    op.create_table(
        "directory_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("directory_id", sa.Uuid(), nullable=False),
        sa.Column("dn", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("sam_account_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("mail", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("last_logon", sa.DateTime(), nullable=True),
        sa.Column("account_disabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("raw_attributes", JSONB(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["directory_id"], ["directories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_directory_users_sam_account_name", "directory_users", ["sam_account_name"])
    op.create_index("ix_directory_users_directory_id", "directory_users", ["directory_id"])
    op.create_index(
        "ix_directory_users_display_name_trgm",
        "directory_users",
        ["display_name"],
        postgresql_using="gin",
        postgresql_ops={"display_name": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_directory_users_dn_unique",
        "directory_users",
        ["directory_id", "dn"],
        unique=True,
    )

    op.create_table(
        "directory_groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("directory_id", sa.Uuid(), nullable=False),
        sa.Column("dn", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("group_type", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("raw_attributes", JSONB(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["directory_id"], ["directories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_directory_groups_name", "directory_groups", ["name"])
    op.create_index("ix_directory_groups_directory_id", "directory_groups", ["directory_id"])
    op.create_index(
        "ix_directory_groups_dn_unique",
        "directory_groups",
        ["directory_id", "dn"],
        unique=True,
    )

    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("directory_id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("RUNNING", "SUCCESS", "FAILED", name="syncstatus"),
            nullable=False,
        ),
        sa.Column("objects_synced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "sync_type",
            sa.Enum("FULL", "DELTA", name="synctype"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["directory_id"], ["directories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_runs_directory_id", "sync_runs", ["directory_id"])


def downgrade() -> None:
    op.drop_table("sync_runs")
    op.drop_table("directory_groups")
    op.drop_table("directory_users")
    op.drop_table("directories")
    op.execute("DROP TYPE IF EXISTS syncstatus")
    op.execute("DROP TYPE IF EXISTS synctype")
