from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, col, select

from app.db import get_session
from app.models.directory import Directory
from app.models.group import DirectoryGroup
from app.models.membership import EffectiveMembership
from app.models.user import DirectoryUser

router = APIRouter(
    prefix="/api/directories/{directory_id}/users/{user_id}",
    tags=["memberships"],
)


class MembershipUser(BaseModel):
    dn: str
    display_name: str


class MembershipEntry(BaseModel):
    group_dn: str
    group_name: str
    depth: int
    path: list[str]


class MembershipResponse(BaseModel):
    user: MembershipUser
    memberships: list[MembershipEntry]
    total: int
    direct_count: int
    inherited_count: int


@router.get("/memberships", response_model=MembershipResponse)
def get_user_memberships(
    directory_id: uuid.UUID,
    user_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> MembershipResponse:
    """All effective group memberships for a user, sorted by depth ascending."""
    directory = session.get(Directory, directory_id)
    if directory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Directory not found")

    user = session.get(DirectoryUser, user_id)
    if user is None or user.directory_id != directory_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    rows = session.exec(
        select(EffectiveMembership)
        .where(
            EffectiveMembership.directory_id == directory_id,
            EffectiveMembership.user_dn == user.dn,
        )
        .order_by(col(EffectiveMembership.depth).asc())
    ).all()

    group_dns = {r.group_dn for r in rows}
    groups_by_dn: dict[str, DirectoryGroup] = {}
    if group_dns:
        groups = session.exec(
            select(DirectoryGroup).where(
                DirectoryGroup.directory_id == directory_id,
                col(DirectoryGroup.dn).in_(list(group_dns)),
            )
        ).all()
        groups_by_dn = {g.dn: g for g in groups}

    memberships = [
        MembershipEntry(
            group_dn=r.group_dn,
            group_name=groups_by_dn[r.group_dn].name if r.group_dn in groups_by_dn else r.group_dn,
            depth=r.depth,
            path=r.path,
        )
        for r in rows
    ]

    direct_count = sum(1 for m in memberships if m.depth == 0)
    inherited_count = len(memberships) - direct_count

    return MembershipResponse(
        user=MembershipUser(dn=user.dn, display_name=user.display_name),
        memberships=memberships,
        total=len(memberships),
        direct_count=direct_count,
        inherited_count=inherited_count,
    )
