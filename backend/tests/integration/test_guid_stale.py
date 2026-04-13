"""Integration tests for GUID-based identity matching and stale cleanup.

Tests DN-rename scenarios, OU-move scenarios, and stale-marking logic
using controlled database state (no live LDAP required for most tests).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text as sa_text
from sqlmodel import Session, select

from app.models.directory import Directory
from app.models.group import DirectoryGroup
from app.models.membership import EffectiveMembership
from app.models.user import DirectoryUser
from app.services.memberships import materialize_effective_memberships
from app.services.sync import (
    _extract_guid,
    _extract_memberships,
    _mark_stale,
    _upsert_groups,
    _upsert_users,
)

pytestmark = pytest.mark.integration


@pytest.fixture()
def directory(session: Session) -> Directory:
    """A minimal directory record for unit-style integration tests."""
    d = Directory(
        name="GUID-Test",
        host="localhost",
        port=389,
        use_ssl=False,
        bind_dn="cn=admin,dc=test,dc=local",
        bind_password="secret",
        base_dn="dc=test,dc=local",
    )
    session.add(d)
    session.commit()
    session.refresh(d)
    return d


def _make_user_entry(
    dn: str,
    uid: str = "jdoe",
    display_name: str = "Jane Doe",
    guid: str | None = None,
) -> dict:
    entry: dict = {
        "dn": dn,
        "uid": uid,
        "sAMAccountName": uid,
        "displayName": display_name,
        "cn": display_name,
    }
    if guid:
        entry["entryUUID"] = guid
    return entry


def _make_group_entry(
    dn: str,
    cn: str = "team",
    guid: str | None = None,
    members: list[str] | None = None,
) -> dict:
    entry: dict = {
        "dn": dn,
        "cn": cn,
    }
    if guid:
        entry["entryUUID"] = guid
    if members is not None:
        entry["member"] = members
    return entry


# ---------------------------------------------------------------------------
# GUID extraction
# ---------------------------------------------------------------------------


class TestExtractGuid:
    def test_entry_uuid_string(self) -> None:
        guid = _extract_guid({"entryUUID": "550e8400-e29b-41d4-a716-446655440000"})
        assert guid == "550e8400-e29b-41d4-a716-446655440000"

    def test_object_guid_hex(self) -> None:
        raw = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        hex_str = raw.bytes_le.hex()
        guid = _extract_guid({"objectGUID": hex_str})
        assert guid == "550e8400-e29b-41d4-a716-446655440000"

    def test_missing_returns_none(self) -> None:
        assert _extract_guid({}) is None
        assert _extract_guid({"objectGUID": ""}) is None


# ---------------------------------------------------------------------------
# DN-Rename Szenario
# ---------------------------------------------------------------------------


class TestDnRename:
    """When a user's CN changes (e.g. marriage), the GUID stays the same
    but the DN changes. The sync should update the DN on the existing record
    instead of creating a duplicate."""

    def test_user_dn_rename_via_guid(
        self, directory: Directory, session: Session
    ) -> None:
        user_guid = str(uuid.uuid4())
        old_dn = "uid=jane.smith,ou=people,dc=test,dc=local"
        new_dn = "uid=jane.mueller,ou=people,dc=test,dc=local"

        _upsert_users(session, directory.id, [
            _make_user_entry(old_dn, uid="jane.smith", display_name="Jane Smith", guid=user_guid),
        ])

        user = session.exec(
            select(DirectoryUser).where(DirectoryUser.directory_id == directory.id)
        ).first()
        assert user is not None
        assert user.dn == old_dn
        original_id = user.id

        _upsert_users(session, directory.id, [
            _make_user_entry(new_dn, uid="jane.mueller", display_name="Jane Mueller", guid=user_guid),
        ])

        users = session.exec(
            select(DirectoryUser).where(DirectoryUser.directory_id == directory.id)
        ).all()
        assert len(users) == 1, f"Expected 1 user after rename, got {len(users)}"
        assert users[0].id == original_id
        assert users[0].dn == new_dn
        assert users[0].display_name == "Jane Mueller"
        assert users[0].guid == user_guid

    def test_group_dn_rename_via_guid(
        self, directory: Directory, session: Session
    ) -> None:
        group_guid = str(uuid.uuid4())
        old_dn = "cn=old-team,ou=groups,dc=test,dc=local"
        new_dn = "cn=new-team,ou=groups,dc=test,dc=local"

        _upsert_groups(session, directory.id, [
            _make_group_entry(old_dn, cn="old-team", guid=group_guid),
        ])

        group = session.exec(
            select(DirectoryGroup).where(DirectoryGroup.directory_id == directory.id)
        ).first()
        assert group is not None
        original_id = group.id

        _upsert_groups(session, directory.id, [
            _make_group_entry(new_dn, cn="new-team", guid=group_guid),
        ])

        groups = session.exec(
            select(DirectoryGroup).where(DirectoryGroup.directory_id == directory.id)
        ).all()
        assert len(groups) == 1
        assert groups[0].id == original_id
        assert groups[0].dn == new_dn
        assert groups[0].name == "new-team"


# ---------------------------------------------------------------------------
# OU-Verschiebung (move between OUs)
# ---------------------------------------------------------------------------


class TestOuMove:
    """When a user is moved between OUs, only the OU portion of the DN changes.
    GUID matching should still find the existing record."""

    def test_user_ou_move(
        self, directory: Directory, session: Session
    ) -> None:
        user_guid = str(uuid.uuid4())
        sales_dn = "uid=bob,ou=sales,dc=test,dc=local"
        eng_dn = "uid=bob,ou=engineering,dc=test,dc=local"

        _upsert_users(session, directory.id, [
            _make_user_entry(sales_dn, uid="bob", display_name="Bob", guid=user_guid),
        ])

        original = session.exec(
            select(DirectoryUser).where(DirectoryUser.directory_id == directory.id)
        ).first()
        assert original is not None
        original_id = original.id

        _upsert_users(session, directory.id, [
            _make_user_entry(eng_dn, uid="bob", display_name="Bob", guid=user_guid),
        ])

        users = session.exec(
            select(DirectoryUser).where(DirectoryUser.directory_id == directory.id)
        ).all()
        assert len(users) == 1, f"Expected 1 user after OU move, got {len(users)}"
        assert users[0].id == original_id
        assert users[0].dn == eng_dn

    def test_group_ou_move(
        self, directory: Directory, session: Session
    ) -> None:
        group_guid = str(uuid.uuid4())
        old_dn = "cn=devops,ou=it,dc=test,dc=local"
        new_dn = "cn=devops,ou=engineering,dc=test,dc=local"

        _upsert_groups(session, directory.id, [
            _make_group_entry(old_dn, cn="devops", guid=group_guid),
        ])

        original = session.exec(
            select(DirectoryGroup).where(DirectoryGroup.directory_id == directory.id)
        ).first()
        original_id = original.id

        _upsert_groups(session, directory.id, [
            _make_group_entry(new_dn, cn="devops", guid=group_guid),
        ])

        groups = session.exec(
            select(DirectoryGroup).where(DirectoryGroup.directory_id == directory.id)
        ).all()
        assert len(groups) == 1
        assert groups[0].id == original_id
        assert groups[0].dn == new_dn


# ---------------------------------------------------------------------------
# Stale-Markierung bei Löschung
# ---------------------------------------------------------------------------


class TestStaleMarking:
    """Objects not returned by LDAP in a sync run should be marked stale."""

    def test_deleted_user_marked_stale(
        self, directory: Directory, session: Session
    ) -> None:
        guid_a = str(uuid.uuid4())
        guid_b = str(uuid.uuid4())
        old_time = datetime.utcnow() - timedelta(hours=1)

        _upsert_users(session, directory.id, [
            _make_user_entry("uid=a,dc=test", uid="a", display_name="A", guid=guid_a),
            _make_user_entry("uid=b,dc=test", uid="b", display_name="B", guid=guid_b),
        ])

        session.execute(
            sa_text("UPDATE directory_users SET last_seen_at = :ts WHERE directory_id = :did"),
            {"ts": old_time, "did": directory.id},
        )
        session.commit()

        # Second sync only returns user A
        sync_start = datetime.utcnow()
        _upsert_users(session, directory.id, [
            _make_user_entry("uid=a,dc=test", uid="a", display_name="A", guid=guid_a),
        ])

        result = _mark_stale(session, directory.id, sync_start)
        assert result["users"] == 1

        user_b = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == directory.id,
                DirectoryUser.guid == guid_b,
            )
        ).first()
        assert user_b is not None
        assert user_b.stale is True

        user_a = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == directory.id,
                DirectoryUser.guid == guid_a,
            )
        ).first()
        assert user_a is not None
        assert user_a.stale is False

    def test_deleted_group_marked_stale(
        self, directory: Directory, session: Session
    ) -> None:
        guid_a = str(uuid.uuid4())
        guid_b = str(uuid.uuid4())
        old_time = datetime.utcnow() - timedelta(hours=1)

        _upsert_groups(session, directory.id, [
            _make_group_entry("cn=a,dc=test", cn="a", guid=guid_a),
            _make_group_entry("cn=b,dc=test", cn="b", guid=guid_b),
        ])

        session.execute(
            sa_text("UPDATE directory_groups SET last_seen_at = :ts WHERE directory_id = :did"),
            {"ts": old_time, "did": directory.id},
        )
        session.commit()

        sync_start = datetime.utcnow()
        _upsert_groups(session, directory.id, [
            _make_group_entry("cn=a,dc=test", cn="a", guid=guid_a),
        ])

        result = _mark_stale(session, directory.id, sync_start)
        assert result["groups"] == 1

        group_b = session.exec(
            select(DirectoryGroup).where(
                DirectoryGroup.directory_id == directory.id,
                DirectoryGroup.guid == guid_b,
            )
        ).first()
        assert group_b is not None
        assert group_b.stale is True

    def test_stale_flag_cleared_on_reappearance(
        self, directory: Directory, session: Session
    ) -> None:
        """If a previously stale user reappears in LDAP, stale should be reset to False."""
        user_guid = str(uuid.uuid4())

        _upsert_users(session, directory.id, [
            _make_user_entry("uid=x,dc=test", uid="x", display_name="X", guid=user_guid),
        ])

        old_time = datetime.utcnow() - timedelta(hours=1)
        session.execute(
            sa_text("UPDATE directory_users SET last_seen_at = :ts WHERE directory_id = :did"),
            {"ts": old_time, "did": directory.id},
        )
        session.commit()

        sync_start = datetime.utcnow()
        _mark_stale(session, directory.id, sync_start)

        user = session.exec(
            select(DirectoryUser).where(DirectoryUser.guid == user_guid)
        ).first()
        assert user.stale is True

        _upsert_users(session, directory.id, [
            _make_user_entry("uid=x,dc=test", uid="x", display_name="X", guid=user_guid),
        ])

        session.refresh(user)
        assert user.stale is False


# ---------------------------------------------------------------------------
# Stale-Ausschluss aus Effective Memberships
# ---------------------------------------------------------------------------


class TestStaleExcludedFromMemberships:
    """Stale users and groups must not appear in effective_memberships."""

    def test_stale_user_excluded_from_effective(
        self, directory: Directory, session: Session
    ) -> None:
        user_guid = str(uuid.uuid4())
        group_guid = str(uuid.uuid4())
        user_dn = "uid=alice,ou=people,dc=test,dc=local"
        group_dn = "cn=team,ou=groups,dc=test,dc=local"

        _upsert_users(session, directory.id, [
            _make_user_entry(user_dn, uid="alice", display_name="Alice", guid=user_guid),
        ])
        _upsert_groups(session, directory.id, [
            _make_group_entry(group_dn, cn="team", guid=group_guid, members=[user_dn]),
        ])
        _extract_memberships(session, directory.id, [
            _make_group_entry(group_dn, cn="team", guid=group_guid, members=[user_dn]),
        ])

        count = materialize_effective_memberships(directory.id, session)
        assert count == 1

        old_time = datetime.utcnow() - timedelta(hours=1)
        session.execute(
            sa_text("UPDATE directory_users SET last_seen_at = :ts WHERE directory_id = :did"),
            {"ts": old_time, "did": directory.id},
        )
        session.execute(
            sa_text("UPDATE directory_groups SET last_seen_at = :ts WHERE directory_id = :did"),
            {"ts": old_time, "did": directory.id},
        )
        session.commit()

        sync_start = datetime.utcnow()
        _mark_stale(session, directory.id, sync_start)

        user = session.exec(
            select(DirectoryUser).where(DirectoryUser.guid == user_guid)
        ).first()
        assert user.stale is True

        count = materialize_effective_memberships(directory.id, session)
        assert count == 0, "Stale user should be excluded from effective memberships"

        rows = session.exec(
            select(EffectiveMembership).where(
                EffectiveMembership.directory_id == directory.id,
            )
        ).all()
        assert len(rows) == 0

    def test_stale_group_excluded_from_effective(
        self, directory: Directory, session: Session
    ) -> None:
        user_guid = str(uuid.uuid4())
        group_a_guid = str(uuid.uuid4())
        group_b_guid = str(uuid.uuid4())
        user_dn = "uid=bob,ou=people,dc=test,dc=local"
        group_a_dn = "cn=alpha,ou=groups,dc=test,dc=local"
        group_b_dn = "cn=beta,ou=groups,dc=test,dc=local"

        _upsert_users(session, directory.id, [
            _make_user_entry(user_dn, uid="bob", display_name="Bob", guid=user_guid),
        ])
        _upsert_groups(session, directory.id, [
            _make_group_entry(group_a_dn, cn="alpha", guid=group_a_guid, members=[user_dn]),
            _make_group_entry(group_b_dn, cn="beta", guid=group_b_guid, members=[group_a_dn]),
        ])
        group_entries = [
            _make_group_entry(group_a_dn, cn="alpha", guid=group_a_guid, members=[user_dn]),
            _make_group_entry(group_b_dn, cn="beta", guid=group_b_guid, members=[group_a_dn]),
        ]
        _extract_memberships(session, directory.id, group_entries)

        count = materialize_effective_memberships(directory.id, session)
        assert count == 2  # bob→alpha (d=0), bob→beta (d=1)

        session.execute(
            DirectoryGroup.__table__.update()
            .where(DirectoryGroup.guid == group_b_guid)
            .values(stale=True)
        )
        session.commit()

        count = materialize_effective_memberships(directory.id, session)
        assert count == 1, "Only non-stale group alpha should remain"

        rows = session.exec(
            select(EffectiveMembership).where(
                EffectiveMembership.directory_id == directory.id,
            )
        ).all()
        assert len(rows) == 1
        assert rows[0].group_dn == group_a_dn

    def test_stale_parent_group_cuts_chain(
        self, directory: Directory, session: Session
    ) -> None:
        """If a middle group in a chain is stale, the chain should stop there."""
        user_guid = str(uuid.uuid4())
        g1_guid = str(uuid.uuid4())
        g2_guid = str(uuid.uuid4())
        g3_guid = str(uuid.uuid4())
        user_dn = "uid=carol,ou=people,dc=test,dc=local"
        g1_dn = "cn=g1,ou=groups,dc=test,dc=local"
        g2_dn = "cn=g2,ou=groups,dc=test,dc=local"
        g3_dn = "cn=g3,ou=groups,dc=test,dc=local"

        _upsert_users(session, directory.id, [
            _make_user_entry(user_dn, uid="carol", display_name="Carol", guid=user_guid),
        ])
        _upsert_groups(session, directory.id, [
            _make_group_entry(g1_dn, cn="g1", guid=g1_guid, members=[user_dn]),
            _make_group_entry(g2_dn, cn="g2", guid=g2_guid, members=[g1_dn]),
            _make_group_entry(g3_dn, cn="g3", guid=g3_guid, members=[g2_dn]),
        ])
        group_entries = [
            _make_group_entry(g1_dn, cn="g1", guid=g1_guid, members=[user_dn]),
            _make_group_entry(g2_dn, cn="g2", guid=g2_guid, members=[g1_dn]),
            _make_group_entry(g3_dn, cn="g3", guid=g3_guid, members=[g2_dn]),
        ]
        _extract_memberships(session, directory.id, group_entries)

        count_before = materialize_effective_memberships(directory.id, session)
        assert count_before == 3  # carol→g1(d=0), carol→g2(d=1), carol→g3(d=2)

        session.execute(
            DirectoryGroup.__table__.update()
            .where(DirectoryGroup.guid == g2_guid)
            .values(stale=True)
        )
        session.commit()

        count_after = materialize_effective_memberships(directory.id, session)
        assert count_after == 1, "Only g1 (non-stale) should remain"

        rows = session.exec(
            select(EffectiveMembership).where(
                EffectiveMembership.directory_id == directory.id,
            )
        ).all()
        assert len(rows) == 1
        assert rows[0].group_dn == g1_dn
        assert rows[0].depth == 0


# ---------------------------------------------------------------------------
# DN-Fallback (kein GUID)
# ---------------------------------------------------------------------------


class TestDnFallbackWithoutGuid:
    """Without a GUID, the system should fall back to DN-based matching."""

    def test_user_upsert_without_guid_uses_dn(
        self, directory: Directory, session: Session
    ) -> None:
        dn = "uid=legacy,dc=test,dc=local"

        _upsert_users(session, directory.id, [
            _make_user_entry(dn, uid="legacy", display_name="Legacy User"),
        ])

        users = session.exec(
            select(DirectoryUser).where(DirectoryUser.directory_id == directory.id)
        ).all()
        assert len(users) == 1
        original_id = users[0].id

        _upsert_users(session, directory.id, [
            _make_user_entry(dn, uid="legacy", display_name="Legacy User Updated"),
        ])

        users = session.exec(
            select(DirectoryUser).where(DirectoryUser.directory_id == directory.id)
        ).all()
        assert len(users) == 1
        assert users[0].id == original_id
        assert users[0].display_name == "Legacy User Updated"
