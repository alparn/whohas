from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models.directory import Directory

router = APIRouter(prefix="/api/directories", tags=["directories"])


class DirectoryRead(BaseModel):
    id: uuid.UUID
    name: str
    host: str
    port: int
    use_ssl: bool
    base_dn: str
    user_filter: str
    group_filter: str
    last_full_sync_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DirectoryCreate(BaseModel):
    name: str
    host: str
    port: int = 389
    use_ssl: bool = False
    bind_dn: str
    bind_password: str
    base_dn: str
    user_filter: str = "(objectClass=user)"
    group_filter: str = "(objectClass=group)"


class DirectoryUpdate(BaseModel):
    name: str | None = None
    host: str | None = None
    port: int | None = None
    use_ssl: bool | None = None
    bind_dn: str | None = None
    bind_password: str | None = None
    base_dn: str | None = None
    user_filter: str | None = None
    group_filter: str | None = None


@router.get("", response_model=list[DirectoryRead])
def list_directories(session: Session = Depends(get_session)) -> list[Directory]:
    """Return all configured LDAP directories."""
    return list(session.exec(select(Directory)).all())


@router.get("/{directory_id}", response_model=DirectoryRead)
def get_directory(
    directory_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> Directory:
    """Return a single directory by ID."""
    directory = session.get(Directory, directory_id)
    if directory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Directory not found")
    return directory


@router.post("", response_model=DirectoryRead, status_code=status.HTTP_201_CREATED)
def create_directory(
    body: DirectoryCreate,
    session: Session = Depends(get_session),
) -> Directory:
    """Register a new LDAP directory connection."""
    directory = Directory(**body.model_dump())
    session.add(directory)
    session.commit()
    session.refresh(directory)
    return directory


@router.patch("/{directory_id}", response_model=DirectoryRead)
def update_directory(
    directory_id: uuid.UUID,
    body: DirectoryUpdate,
    session: Session = Depends(get_session),
) -> Directory:
    """Partially update a directory's configuration."""
    directory = session.get(Directory, directory_id)
    if directory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Directory not found")

    updates = body.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(directory, key, value)
    directory.updated_at = datetime.utcnow()

    session.add(directory)
    session.commit()
    session.refresh(directory)
    return directory
