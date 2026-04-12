from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlmodel import Session

from app.db import get_session
from app.models.group import DirectoryGroup
from app.models.membership import EffectiveMembership

router = APIRouter(prefix="/api/directories/{directory_id}/groups", tags=["groups"])


class GroupRead(BaseModel):
    id: uuid.UUID
    directory_id: uuid.UUID
    dn: str
    name: str
    description: str | None
    group_type: str | None
    first_seen_at: datetime
    last_seen_at: datetime


class GroupDetailRead(GroupRead):
    effective_member_count: int
    direct_member_count: int


class GroupMemberRead(BaseModel):
    user_dn: str
    display_name: str
    sam_account_name: str
    mail: str | None
    depth: int


@router.get("", response_model=list[GroupRead])
def list_groups(
    directory_id: uuid.UUID,
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> list[DirectoryGroup]:
    base = select(DirectoryGroup).where(DirectoryGroup.directory_id == directory_id)

    if q.strip():
        base = base.where(DirectoryGroup.name.ilike(f"%{q.strip()}%"))  # type: ignore[union-attr]

    base = base.order_by(DirectoryGroup.name.asc()).limit(limit)  # type: ignore[union-attr]
    return list(session.execute(base).scalars().all())


@router.get("/{group_id}", response_model=GroupDetailRead)
def get_group(
    directory_id: uuid.UUID,
    group_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> GroupDetailRead:
    group = session.get(DirectoryGroup, group_id)
    if group is None or group.directory_id != directory_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    effective_count: int = session.scalar(
        select(func.count()).select_from(EffectiveMembership).where(
            EffectiveMembership.directory_id == directory_id,
            EffectiveMembership.group_dn == group.dn,
        )
    ) or 0

    from app.models.membership import DirectMembership, ChildType

    direct_count: int = session.scalar(
        select(func.count()).select_from(DirectMembership).where(
            DirectMembership.directory_id == directory_id,
            DirectMembership.parent_dn == group.dn,
            DirectMembership.child_type == ChildType.USER,
        )
    ) or 0

    return GroupDetailRead(
        id=group.id,
        directory_id=group.directory_id,
        dn=group.dn,
        name=group.name,
        description=group.description,
        group_type=group.group_type,
        first_seen_at=group.first_seen_at,
        last_seen_at=group.last_seen_at,
        effective_member_count=effective_count,
        direct_member_count=direct_count,
    )


@router.get("/{group_id}/members", response_model=list[GroupMemberRead])
def get_group_members(
    directory_id: uuid.UUID,
    group_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[GroupMemberRead]:
    group = session.get(DirectoryGroup, group_id)
    if group is None or group.directory_id != directory_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    from app.models.user import DirectoryUser

    rows = session.execute(
        select(
            EffectiveMembership.user_dn,
            DirectoryUser.display_name,
            DirectoryUser.sam_account_name,
            DirectoryUser.mail,
            func.min(EffectiveMembership.depth).label("depth"),
        )
        .join(DirectoryUser, DirectoryUser.dn == EffectiveMembership.user_dn)
        .where(
            EffectiveMembership.directory_id == directory_id,
            EffectiveMembership.group_dn == group.dn,
            DirectoryUser.directory_id == directory_id,
        )
        .group_by(
            EffectiveMembership.user_dn,
            DirectoryUser.display_name,
            DirectoryUser.sam_account_name,
            DirectoryUser.mail,
        )
        .order_by(DirectoryUser.display_name.asc())
        .limit(limit)
    ).all()

    return [
        GroupMemberRead(
            user_dn=r.user_dn,
            display_name=r.display_name,
            sam_account_name=r.sam_account_name,
            mail=r.mail,
            depth=r.depth,
        )
        for r in rows
    ]
