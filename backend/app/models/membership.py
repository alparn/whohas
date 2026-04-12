from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class ChildType(str, enum.Enum):
    USER = "user"
    GROUP = "group"


class DirectMembership(SQLModel, table=True):
    __tablename__ = "direct_memberships"
    __table_args__ = (
        UniqueConstraint("directory_id", "parent_dn", "child_dn", name="uq_direct_membership"),
        Index("ix_direct_memberships_parent_dn", "directory_id", "parent_dn"),
        Index("ix_direct_memberships_child_dn", "directory_id", "child_dn"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    directory_id: uuid.UUID = Field(foreign_key="directories.id", index=True)
    parent_dn: str
    child_dn: str
    child_type: ChildType
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EffectiveMembership(SQLModel, table=True):
    """Flattened transitive closure — one row per (user, group, path) triple.

    Variante B: stores every distinct path through the group hierarchy.
    A user can appear multiple times for the same group if reachable
    via different nesting paths (e.g. diamond pattern). This preserves
    the full audit trail needed for permissions analysis.
    """

    __tablename__ = "effective_memberships"
    __table_args__ = (
        Index("ix_effective_memberships_user", "directory_id", "user_dn"),
        Index("ix_effective_memberships_group", "directory_id", "group_dn"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    directory_id: uuid.UUID = Field(foreign_key="directories.id", index=True)
    user_dn: str
    group_dn: str
    depth: int
    path: list[str] = Field(default_factory=list, sa_column=Column(JSONB, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
