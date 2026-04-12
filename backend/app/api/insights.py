from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db import get_session
from app.models.directory import Directory
from app.schemas.insights import (
    GroupResponse,
    LargestGroupResponse,
    StaleUserResponse,
    SummaryResponse,
)
from app.services.insights import (
    get_disabled_users_in_groups,
    get_empty_groups,
    get_largest_groups,
    get_stale_users,
    get_summary,
)

router = APIRouter(
    prefix="/api/directories/{directory_id}/insights",
    tags=["insights"],
)


def _require_directory(directory_id: uuid.UUID, session: Session) -> Directory:
    d = session.get(Directory, directory_id)
    if d is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Directory not found")
    return d


@router.get("/summary", response_model=SummaryResponse)
def summary_endpoint(
    directory_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> SummaryResponse:
    _require_directory(directory_id, session)
    return get_summary(session, directory_id)


@router.get("/stale-users", response_model=list[StaleUserResponse])
def stale_users_endpoint(
    directory_id: uuid.UUID,
    limit: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[StaleUserResponse]:
    _require_directory(directory_id, session)
    return get_stale_users(session, directory_id, limit=limit)


@router.get("/empty-groups", response_model=list[GroupResponse])
def empty_groups_endpoint(
    directory_id: uuid.UUID,
    limit: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[GroupResponse]:
    _require_directory(directory_id, session)
    return get_empty_groups(session, directory_id, limit=limit)


@router.get("/largest-groups", response_model=list[LargestGroupResponse])
def largest_groups_endpoint(
    directory_id: uuid.UUID,
    limit: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[LargestGroupResponse]:
    _require_directory(directory_id, session)
    return get_largest_groups(session, directory_id, limit=limit)


@router.get("/disabled-in-groups", response_model=list[StaleUserResponse])
def disabled_in_groups_endpoint(
    directory_id: uuid.UUID,
    limit: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[StaleUserResponse]:
    _require_directory(directory_id, session)
    return get_disabled_users_in_groups(session, directory_id, limit=limit)
