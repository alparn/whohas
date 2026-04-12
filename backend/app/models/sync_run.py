from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class SyncStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class SyncType(str, enum.Enum):
    FULL = "full"
    DELTA = "delta"


class SyncRun(SQLModel, table=True):
    __tablename__ = "sync_runs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    directory_id: uuid.UUID = Field(foreign_key="directories.id", index=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = Field(default=None)
    status: SyncStatus = Field(default=SyncStatus.RUNNING)
    objects_synced: int = Field(default=0)
    error_message: str | None = Field(default=None)
    sync_type: SyncType = Field(default=SyncType.FULL)
