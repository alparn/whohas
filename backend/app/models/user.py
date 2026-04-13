from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class DirectoryUser(SQLModel, table=True):
    __tablename__ = "directory_users"
    __table_args__ = (
        Index(
            "ix_directory_users_display_name_trgm",
            "display_name",
            postgresql_using="gin",
            postgresql_ops={"display_name": "gin_trgm_ops"},
        ),
        Index("ix_directory_users_dn_unique", "directory_id", "dn", unique=True),
        Index("ix_directory_users_guid", "directory_id", "guid"),
        UniqueConstraint("directory_id", "guid", name="uq_directory_users_directory_id_guid"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    directory_id: uuid.UUID = Field(foreign_key="directories.id", index=True)
    dn: str
    guid: str | None = Field(default=None)
    sam_account_name: str = Field(index=True)
    display_name: str = Field(sa_column=Column(Text, nullable=False))
    mail: str | None = Field(default=None)
    last_logon: datetime | None = Field(default=None)
    account_disabled: bool = Field(default=False)
    stale: bool = Field(default=False)
    raw_attributes: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
