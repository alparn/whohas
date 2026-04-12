from __future__ import annotations

import uuid

from sqlalchemy import func, select, text
from sqlmodel import Session

from app.models.group import DirectoryGroup
from app.models.membership import EffectiveMembership
from app.models.user import DirectoryUser
from app.schemas.insights import (
    GroupResponse,
    LargestGroupResponse,
    StaleUserResponse,
    SummaryResponse,
)

STALE_THRESHOLD_DAYS = 90


def get_summary(session: Session, directory_id: uuid.UUID) -> SummaryResponse:
    total_users = session.scalar(
        select(func.count()).select_from(DirectoryUser).where(
            DirectoryUser.directory_id == directory_id
        )
    ) or 0

    total_groups = session.scalar(
        select(func.count()).select_from(DirectoryGroup).where(
            DirectoryGroup.directory_id == directory_id
        )
    ) or 0

    stale_user_count = session.scalar(
        select(func.count()).select_from(DirectoryUser).where(
            DirectoryUser.directory_id == directory_id,
            DirectoryUser.account_disabled == False,  # noqa: E712
            (
                (DirectoryUser.last_logon < func.now() - text(f"interval '{STALE_THRESHOLD_DAYS} days'"))
                | (DirectoryUser.last_logon.is_(None))  # type: ignore[union-attr]
            ),
        )
    ) or 0

    empty_group_count = session.scalar(
        select(func.count()).select_from(DirectoryGroup).where(
            DirectoryGroup.directory_id == directory_id,
            ~DirectoryGroup.dn.in_(  # type: ignore[union-attr]
                select(EffectiveMembership.group_dn).where(
                    EffectiveMembership.directory_id == directory_id
                ).distinct()
            ),
        )
    ) or 0

    disabled_in_groups_count = session.scalar(
        select(func.count()).select_from(DirectoryUser).where(
            DirectoryUser.directory_id == directory_id,
            DirectoryUser.account_disabled == True,  # noqa: E712
            DirectoryUser.dn.in_(  # type: ignore[union-attr]
                select(EffectiveMembership.user_dn).where(
                    EffectiveMembership.directory_id == directory_id
                ).distinct()
            ),
        )
    ) or 0

    return SummaryResponse(
        total_users=total_users,
        total_groups=total_groups,
        stale_user_count=stale_user_count,
        empty_group_count=empty_group_count,
        disabled_in_groups_count=disabled_in_groups_count,
    )


def get_stale_users(
    session: Session, directory_id: uuid.UUID, limit: int = 10
) -> list[StaleUserResponse]:
    rows = session.execute(
        select(DirectoryUser)
        .where(
            DirectoryUser.directory_id == directory_id,
            DirectoryUser.account_disabled == False,  # noqa: E712
            (
                (DirectoryUser.last_logon < func.now() - text(f"interval '{STALE_THRESHOLD_DAYS} days'"))
                | (DirectoryUser.last_logon.is_(None))  # type: ignore[union-attr]
            ),
        )
        .order_by(
            DirectoryUser.last_logon.asc().nulls_first(),  # type: ignore[union-attr]
        )
        .limit(limit)
    ).scalars().all()

    return [
        StaleUserResponse(
            id=u.id,
            dn=u.dn,
            display_name=u.display_name,
            sam_account_name=u.sam_account_name,
            mail=u.mail,
            last_logon=u.last_logon,
            account_disabled=u.account_disabled,
        )
        for u in rows
    ]


def get_empty_groups(
    session: Session, directory_id: uuid.UUID, limit: int = 10
) -> list[GroupResponse]:
    rows = session.execute(
        select(DirectoryGroup)
        .where(
            DirectoryGroup.directory_id == directory_id,
            ~DirectoryGroup.dn.in_(  # type: ignore[union-attr]
                select(EffectiveMembership.group_dn).where(
                    EffectiveMembership.directory_id == directory_id
                ).distinct()
            ),
        )
        .order_by(DirectoryGroup.name.asc())  # type: ignore[union-attr]
        .limit(limit)
    ).scalars().all()

    return [
        GroupResponse(id=g.id, dn=g.dn, name=g.name, description=g.description)
        for g in rows
    ]


def get_largest_groups(
    session: Session, directory_id: uuid.UUID, limit: int = 10
) -> list[LargestGroupResponse]:
    member_count = (
        select(func.count())
        .where(
            EffectiveMembership.directory_id == directory_id,
            EffectiveMembership.group_dn == DirectoryGroup.dn,
        )
        .correlate(DirectoryGroup)
        .scalar_subquery()
        .label("effective_member_count")
    )

    rows = session.exec(
        select(DirectoryGroup, member_count)
        .where(DirectoryGroup.directory_id == directory_id)
        .order_by(member_count.desc())
        .limit(limit)
    ).all()

    return [
        LargestGroupResponse(
            id=g.id,
            dn=g.dn,
            name=g.name,
            description=g.description,
            effective_member_count=cnt,
        )
        for g, cnt in rows
    ]


def get_disabled_users_in_groups(
    session: Session, directory_id: uuid.UUID, limit: int = 10
) -> list[StaleUserResponse]:
    rows = session.execute(
        select(DirectoryUser)
        .where(
            DirectoryUser.directory_id == directory_id,
            DirectoryUser.account_disabled == True,  # noqa: E712
            DirectoryUser.dn.in_(  # type: ignore[union-attr]
                select(EffectiveMembership.user_dn).where(
                    EffectiveMembership.directory_id == directory_id
                ).distinct()
            ),
        )
        .order_by(DirectoryUser.display_name.asc())  # type: ignore[union-attr]
        .limit(limit)
    ).scalars().all()

    return [
        StaleUserResponse(
            id=u.id,
            dn=u.dn,
            display_name=u.display_name,
            sam_account_name=u.sam_account_name,
            mail=u.mail,
            last_logon=u.last_logon,
            account_disabled=u.account_disabled,
        )
        for u in rows
    ]
