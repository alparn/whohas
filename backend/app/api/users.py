from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.models.user import DirectoryUser

router = APIRouter(prefix="/api/directories/{directory_id}/users", tags=["users"])


class UserRead(BaseModel):
    id: uuid.UUID
    directory_id: uuid.UUID
    dn: str
    sam_account_name: str
    display_name: str
    mail: str | None
    last_logon: datetime | None
    account_disabled: bool
    first_seen_at: datetime
    last_seen_at: datetime


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    directory_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> DirectoryUser:
    """Return a single user by ID."""
    user = session.get(DirectoryUser, user_id)
    if user is None or user.directory_id != directory_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("", response_model=list[UserRead])
def search_users(
    directory_id: uuid.UUID,
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[DirectoryUser]:
    """Search cached directory users by display_name using trigram similarity.

    If *q* is empty, returns the most recently seen users.
    """
    base = select(DirectoryUser).where(DirectoryUser.directory_id == directory_id)

    if q.strip():
        base = (
            base
            .where(func.similarity(DirectoryUser.display_name, q) > 0.1)
            .order_by(func.similarity(DirectoryUser.display_name, q).desc())
        )
    else:
        base = base.order_by(DirectoryUser.last_seen_at.desc())  # type: ignore[union-attr]

    base = base.limit(limit)
    return list(session.exec(base).all())
