from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class DirectoryGroup(SQLModel, table=True):
    __tablename__ = "directory_groups"
    __table_args__ = (
        Index("ix_directory_groups_dn_unique", "directory_id", "dn", unique=True),
        Index("ix_directory_groups_guid", "directory_id", "guid"),
        UniqueConstraint("directory_id", "guid", name="uq_directory_groups_directory_id_guid"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    directory_id: uuid.UUID = Field(foreign_key="directories.id", index=True)
    dn: str
    guid: str | None = Field(default=None)
    name: str = Field(index=True)
    description: str | None = Field(default=None)
    group_type: str | None = Field(default=None)
    stale: bool = Field(default=False)
    raw_attributes: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
