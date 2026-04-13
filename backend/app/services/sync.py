from __future__ import annotations

import logging
import traceback
import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from sqlalchemy import text

from app.db import engine
from app.events import notify
from app.models.directory import Directory
from app.models.group import DirectoryGroup
from app.models.membership import ChildType, DirectMembership
from app.models.sync_run import SyncRun, SyncStatus, SyncType
from app.models.user import DirectoryUser
from app.services.ldap_client import LDAPClient
from app.services.memberships import materialize_effective_memberships

logger = logging.getLogger(__name__)

# AD userAccountControl flag for disabled accounts
_UAC_ACCOUNTDISABLE = 0x0002


def _extract_guid(entry: dict[str, Any]) -> str | None:
    """Extract a stable GUID from an LDAP entry.

    AD delivers ``objectGUID`` as raw bytes (which ldap3 + _make_json_safe
    turns into a hex string).  OpenLDAP delivers ``entryUUID`` as a plain
    UUID string.
    """
    for key in ("objectGUID", "entryUUID"):
        val = entry.get(key)
        if not val:
            continue
        if isinstance(val, bytes):
            return str(uuid.UUID(bytes_le=val))
        s = str(val)
        if len(s) == 32 and all(c in "0123456789abcdefABCDEF" for c in s):
            # hex-encoded bytes produced by _make_json_safe for objectGUID
            return str(uuid.UUID(bytes_le=bytes.fromhex(s)))
        try:
            return str(uuid.UUID(s))
        except ValueError:
            logger.warning("Ignoring unparseable GUID value %r from key %s", val, key)
    return None


def sync_directory(directory_id: uuid.UUID) -> None:
    """Run a full LDAP sync for the given directory.

    Reads user_filter and group_filter from the Directory record so
    production and tests use the same code path.
    """
    with Session(engine) as session:
        directory = session.get(Directory, directory_id)
        if directory is None:
            logger.error("Directory %s not found — skipping sync", directory_id)
            return

        run = SyncRun(directory_id=directory.id, sync_type=SyncType.FULL)
        session.add(run)
        session.commit()
        session.refresh(run)

        client = LDAPClient(
            directory,
            user_filter=directory.user_filter,
            group_filter=directory.group_filter,
        )
        try:
            client.connect()
            sync_started_at = datetime.utcnow()

            users = client.search_users()
            user_count = _upsert_users(session, directory.id, users)

            groups = client.search_groups()
            group_count = _upsert_groups(session, directory.id, groups)

            stale_counts = _mark_stale(session, directory.id, sync_started_at)

            _extract_memberships(session, directory.id, groups)
            membership_count = materialize_effective_memberships(directory.id, session)

            run.status = SyncStatus.SUCCESS
            run.objects_synced = user_count + group_count
            run.finished_at = datetime.utcnow()
            directory.last_full_sync_at = run.finished_at
            session.add(run)
            session.add(directory)
            session.commit()

            notify("sync_completed", {
                "directory_id": str(directory.id),
                "sync_run_id": str(run.id),
                "users": user_count,
                "groups": group_count,
                "effective_memberships": membership_count,
                "stale_users": stale_counts["users"],
                "stale_groups": stale_counts["groups"],
            })
            logger.info(
                "Sync completed for %s — %d users, %d groups, "
                "%d stale users, %d stale groups",
                directory.name,
                user_count,
                group_count,
                stale_counts["users"],
                stale_counts["groups"],
            )

        except Exception:
            logger.exception("Sync failed for directory %s", directory.name)
            run.status = SyncStatus.FAILED
            run.finished_at = datetime.utcnow()
            run.error_message = traceback.format_exc()
            session.add(run)
            session.commit()

            notify("sync_failed", {
                "directory_id": str(directory.id),
                "sync_run_id": str(run.id),
            })
        finally:
            client.disconnect()


def sync_all_directories() -> None:
    """Sync every registered directory. Called by the scheduler."""
    with Session(engine) as session:
        directories = session.exec(select(Directory)).all()

    for directory in directories:
        try:
            sync_directory(directory.id)
        except Exception:
            logger.exception("Unhandled error syncing directory %s", directory.id)


def _upsert_users(
    session: Session,
    directory_id: uuid.UUID,
    entries: list[dict[str, Any]],
) -> int:
    """Upsert user entries into directory_users. Returns count of upserted rows."""
    now = datetime.utcnow()
    count = 0

    for entry in entries:
        dn = entry.get("dn", "")
        if not dn:
            continue

        guid = _extract_guid(entry)

        # GUID-first lookup, DN-fallback
        existing: DirectoryUser | None = None
        if guid:
            existing = session.exec(
                select(DirectoryUser).where(
                    DirectoryUser.directory_id == directory_id,
                    DirectoryUser.guid == guid,
                )
            ).first()

        if existing is None:
            existing = session.exec(
                select(DirectoryUser).where(
                    DirectoryUser.directory_id == directory_id,
                    DirectoryUser.dn == dn,
                )
            ).first()

        uac = _safe_int(entry.get("userAccountControl", 0))
        disabled = bool(uac & _UAC_ACCOUNTDISABLE)

        last_logon_raw = entry.get("lastLogon")
        last_logon = _parse_ad_timestamp(last_logon_raw) if last_logon_raw else None

        sam = str(entry.get("sAMAccountName", "") or entry.get("uid", ""))

        if existing:
            existing.dn = dn
            existing.guid = guid or existing.guid
            existing.sam_account_name = sam
            existing.display_name = str(entry.get("displayName", entry.get("cn", "")))
            existing.mail = entry.get("mail")
            existing.last_logon = last_logon
            existing.account_disabled = disabled
            existing.stale = False
            existing.raw_attributes = entry
            existing.last_seen_at = now
            session.add(existing)
        else:
            user = DirectoryUser(
                directory_id=directory_id,
                dn=dn,
                guid=guid,
                sam_account_name=sam,
                display_name=str(entry.get("displayName", entry.get("cn", ""))),
                mail=entry.get("mail"),
                last_logon=last_logon,
                account_disabled=disabled,
                raw_attributes=entry,
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(user)
        count += 1

    session.commit()
    return count


def _upsert_groups(
    session: Session,
    directory_id: uuid.UUID,
    entries: list[dict[str, Any]],
) -> int:
    """Upsert group entries into directory_groups. Returns count of upserted rows."""
    now = datetime.utcnow()
    count = 0

    for entry in entries:
        dn = entry.get("dn", "")
        if not dn:
            continue

        guid = _extract_guid(entry)

        # GUID-first lookup, DN-fallback
        existing: DirectoryGroup | None = None
        if guid:
            existing = session.exec(
                select(DirectoryGroup).where(
                    DirectoryGroup.directory_id == directory_id,
                    DirectoryGroup.guid == guid,
                )
            ).first()

        if existing is None:
            existing = session.exec(
                select(DirectoryGroup).where(
                    DirectoryGroup.directory_id == directory_id,
                    DirectoryGroup.dn == dn,
                )
            ).first()

        if existing:
            existing.dn = dn
            existing.guid = guid or existing.guid
            existing.name = str(entry.get("cn", entry.get("name", "")))
            existing.description = entry.get("description")
            existing.group_type = str(entry.get("groupType", "")) or None
            existing.stale = False
            existing.raw_attributes = entry
            existing.last_seen_at = now
            session.add(existing)
        else:
            group = DirectoryGroup(
                directory_id=directory_id,
                dn=dn,
                guid=guid,
                name=str(entry.get("cn", entry.get("name", ""))),
                description=entry.get("description"),
                group_type=str(entry.get("groupType", "")) or None,
                raw_attributes=entry,
                first_seen_at=now,
                last_seen_at=now,
            )
            session.add(group)
        count += 1

    session.commit()
    return count


def _mark_stale(
    session: Session,
    directory_id: uuid.UUID,
    sync_started_at: datetime,
) -> dict[str, int]:
    """Mark users/groups not seen during this sync run as stale.

    Any row whose ``last_seen_at`` is older than *sync_started_at* was not
    returned by LDAP and is therefore considered stale.  Returns a dict with
    the number of newly stale users and groups.
    """
    user_result = session.execute(
        text("""
            UPDATE directory_users
            SET stale = true
            WHERE directory_id = :did
              AND last_seen_at < :cutoff
              AND stale = false
        """),
        {"did": directory_id, "cutoff": sync_started_at},
    )
    group_result = session.execute(
        text("""
            UPDATE directory_groups
            SET stale = true
            WHERE directory_id = :did
              AND last_seen_at < :cutoff
              AND stale = false
        """),
        {"did": directory_id, "cutoff": sync_started_at},
    )
    session.commit()

    stale_users = user_result.rowcount  # type: ignore[union-attr]
    stale_groups = group_result.rowcount  # type: ignore[union-attr]

    if stale_users or stale_groups:
        logger.info(
            "Marked %d users and %d groups as stale for directory %s",
            stale_users,
            stale_groups,
            directory_id,
        )

    return {"users": stale_users, "groups": stale_groups}


def _extract_memberships(
    session: Session,
    directory_id: uuid.UUID,
    group_entries: list[dict[str, Any]],
) -> int:
    """Parse member attributes from groups and populate direct_memberships.

    Wipes existing rows for the directory and bulk-inserts fresh data.
    Returns the number of memberships inserted.
    """
    session.execute(
        text("DELETE FROM direct_memberships WHERE directory_id = :did"),
        {"did": directory_id},
    )
    session.flush()

    user_dns: set[str] = set(
        session.exec(
            select(DirectoryUser.dn).where(DirectoryUser.directory_id == directory_id)
        ).all()
    )
    group_dns: set[str] = set(
        session.exec(
            select(DirectoryGroup.dn).where(DirectoryGroup.directory_id == directory_id)
        ).all()
    )

    rows: list[DirectMembership] = []
    now = datetime.utcnow()

    for entry in group_entries:
        parent_dn = entry.get("dn", "")
        if not parent_dn:
            continue

        members = entry.get("member", [])
        if isinstance(members, str):
            members = [members]

        for member_dn in members:
            if not member_dn or member_dn == parent_dn:
                continue

            if member_dn in user_dns:
                child_type = ChildType.USER
            elif member_dn in group_dns:
                child_type = ChildType.GROUP
            else:
                logger.warning(
                    "Member DN %s in group %s is neither a known user nor group — skipping",
                    member_dn,
                    parent_dn,
                )
                continue

            rows.append(
                DirectMembership(
                    directory_id=directory_id,
                    parent_dn=parent_dn,
                    child_dn=member_dn,
                    child_type=child_type,
                    created_at=now,
                )
            )

    session.add_all(rows)
    session.commit()

    logger.info(
        "Extracted %d direct memberships for directory %s",
        len(rows),
        directory_id,
    )
    return len(rows)


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _parse_ad_timestamp(value: Any) -> datetime | None:
    """Convert AD lastLogon to datetime.

    Handles three representations:
    - int / numeric string: Windows FILETIME (100-ns ticks since 1601-01-01)
    - datetime object: already converted by ldap3 for Samba AD
    - ISO-format string: produced by _make_json_safe from a datetime
    """
    if isinstance(value, datetime):
        naive = value.replace(tzinfo=None) if value.tzinfo else value
        if naive.year <= 1601:
            return None
        return naive

    if isinstance(value, str) and "T" in value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
            if parsed.year <= 1601:
                return None
            return parsed
        except ValueError:
            pass

    try:
        ticks = int(value)
        if ticks <= 0:
            return None
        epoch_diff = 116_444_736_000_000_000
        ts = (ticks - epoch_diff) / 10_000_000
        return datetime.utcfromtimestamp(ts)
    except (TypeError, ValueError, OSError):
        return None
