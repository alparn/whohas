from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_users: int
    total_groups: int
    stale_user_count: int
    empty_group_count: int
    disabled_in_groups_count: int


class StaleUserResponse(BaseModel):
    id: uuid.UUID
    dn: str
    display_name: str
    sam_account_name: str
    mail: str | None
    last_logon: datetime | None
    account_disabled: bool


class GroupResponse(BaseModel):
    id: uuid.UUID
    dn: str
    name: str
    description: str | None


class LargestGroupResponse(BaseModel):
    id: uuid.UUID
    dn: str
    name: str
    description: str | None
    effective_member_count: int
