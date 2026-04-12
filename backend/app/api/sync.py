from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlmodel import Session, col, select

from app.db import get_session
from app.models.directory import Directory
from app.models.sync_run import SyncRun, SyncStatus, SyncType
from app.services.sync import sync_directory

router = APIRouter(
    prefix="/api/directories/{directory_id}",
    tags=["sync"],
)


class SyncRunRead(BaseModel):
    id: uuid.UUID
    directory_id: uuid.UUID
    started_at: datetime
    finished_at: datetime | None
    status: SyncStatus
    objects_synced: int
    error_message: str | None
    sync_type: SyncType


class SyncTriggerResponse(BaseModel):
    sync_run_id: uuid.UUID
    status: str


def _get_directory_or_404(
    directory_id: uuid.UUID, session: Session
) -> Directory:
    directory = session.get(Directory, directory_id)
    if directory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Directory not found"
        )
    return directory


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def trigger_sync(
    directory_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """Trigger a full LDAP sync for the given directory.

    Returns immediately with 202 — the sync runs in a background thread.
    Poll GET .../sync-runs/latest to check progress.
    """
    _get_directory_or_404(directory_id, session)

    asyncio.create_task(run_in_threadpool(sync_directory, directory_id))

    return {"status": "started", "directory_id": str(directory_id)}


@router.get("/sync-runs/latest", response_model=SyncRunRead)
def get_latest_sync_run(
    directory_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> SyncRun:
    """Return the most recent sync run for the directory."""
    _get_directory_or_404(directory_id, session)

    stmt = (
        select(SyncRun)
        .where(SyncRun.directory_id == directory_id)
        .order_by(col(SyncRun.started_at).desc())
        .limit(1)
    )
    run = session.exec(stmt).first()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sync runs found for this directory",
        )
    return run


@router.get("/sync-runs", response_model=list[SyncRunRead])
def list_sync_runs(
    directory_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[SyncRun]:
    """Return recent sync runs for the directory."""
    _get_directory_or_404(directory_id, session)

    stmt = (
        select(SyncRun)
        .where(SyncRun.directory_id == directory_id)
        .order_by(col(SyncRun.started_at).desc())
        .limit(limit)
    )
    return list(session.exec(stmt).all())
