from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class Directory(SQLModel, table=True):
    __tablename__ = "directories"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True)
    host: str
    port: int = Field(default=389)
    use_ssl: bool = Field(default=False)
    bind_dn: str
    bind_password: str
    base_dn: str
    user_filter: str = Field(default="(objectClass=user)")
    group_filter: str = Field(default="(objectClass=group)")
    last_full_sync_at: datetime | None = Field(default=None)
    last_usn: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
