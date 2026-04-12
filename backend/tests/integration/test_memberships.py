"""Integration tests for memberships: extraction, materialization, and API endpoints.

All tests run against the existing OpenLDAP fixture with 15 users and 8 groups.
"""

from __future__ import annotations

import pytest
from sqlmodel import Session, select

from app.models.directory import Directory
from app.models.group import DirectoryGroup
from app.models.membership import ChildType, DirectMembership, EffectiveMembership
from app.models.user import DirectoryUser
from app.services.sync import sync_directory

pytestmark = pytest.mark.integration

DN_SUFFIX = ",ou=people,dc=test,dc=local"
GRP_SUFFIX = ",ou=groups,dc=test,dc=local"


def _dn(uid: str) -> str:
    return f"uid={uid}{DN_SUFFIX}"


def _gdn(cn: str) -> str:
    return f"cn={cn}{GRP_SUFFIX}"


class TestDirectMemberships:
    def test_direct_memberships_extracted(
        self, test_directory: Directory, session: Session
    ) -> None:
        """After sync, direct_memberships should contain expected parent-child pairs."""
        sync_directory(test_directory.id)

        all_dm = session.exec(
            select(DirectMembership).where(
                DirectMembership.directory_id == test_directory.id
            )
        ).all()

        # flat-team has 5 user children
        flat_team_children = [
            m for m in all_dm if m.parent_dn == _gdn("flat-team")
        ]
        assert len(flat_team_children) == 5, (
            f"flat-team should have 5 members, got {len(flat_team_children)}: "
            f"{[m.child_dn for m in flat_team_children]}"
        )
        assert all(m.child_type == ChildType.USER for m in flat_team_children)

        # engineering-all has backend-team as a GROUP child
        eng_children = [
            m for m in all_dm if m.parent_dn == _gdn("engineering-all")
        ]
        assert len(eng_children) == 1
        assert eng_children[0].child_dn == _gdn("backend-team")
        assert eng_children[0].child_type == ChildType.GROUP

        # backend-team has database-experts (group) + hannah.fischer (user)
        bt_children = [
            m for m in all_dm if m.parent_dn == _gdn("backend-team")
        ]
        assert len(bt_children) == 2
        child_dns = {m.child_dn for m in bt_children}
        assert _gdn("database-experts") in child_dns
        assert _dn("hannah.fischer") in child_dns

        # empty-group self-reference should be skipped
        empty_children = [
            m for m in all_dm if m.parent_dn == _gdn("empty-group")
        ]
        assert len(empty_children) == 0, (
            f"empty-group self-reference should be skipped, got {len(empty_children)}"
        )

        # Total: 5 (flat) + 0 (empty) + 2 (db-experts) + 2 (backend) +
        #         1 (eng-all) + 2 (marketing) + 2 (all-staff) + 1 (single) = 15
        assert len(all_dm) == 15, f"Expected 15 direct memberships, got {len(all_dm)}"


class TestEffectiveMembershipsNestedChain:
    def test_effective_memberships_for_nested_chain(
        self, test_directory: Directory, session: Session
    ) -> None:
        """alice.wong at the bottom of the chain should have memberships at depths 0-3."""
        sync_directory(test_directory.id)

        alice_dn = _dn("alice.wong")
        rows = session.exec(
            select(EffectiveMembership).where(
                EffectiveMembership.directory_id == test_directory.id,
                EffectiveMembership.user_dn == alice_dn,
            )
        ).all()

        groups_by_depth = {}
        for r in rows:
            groups_by_depth.setdefault(r.depth, []).append(r)

        # depth 0: database-experts (direct)
        assert len(groups_by_depth.get(0, [])) == 1
        assert groups_by_depth[0][0].group_dn == _gdn("database-experts")
        assert groups_by_depth[0][0].path == [_gdn("database-experts")]

        # depth 1: backend-team
        assert len(groups_by_depth.get(1, [])) == 1
        assert groups_by_depth[1][0].group_dn == _gdn("backend-team")
        assert groups_by_depth[1][0].path == [
            _gdn("database-experts"),
            _gdn("backend-team"),
        ]

        # depth 2: engineering-all
        assert len(groups_by_depth.get(2, [])) == 1
        assert groups_by_depth[2][0].group_dn == _gdn("engineering-all")
        assert groups_by_depth[2][0].path == [
            _gdn("database-experts"),
            _gdn("backend-team"),
            _gdn("engineering-all"),
        ]

        # depth 3: all-staff
        assert len(groups_by_depth.get(3, [])) == 1
        assert groups_by_depth[3][0].group_dn == _gdn("all-staff")
        assert groups_by_depth[3][0].path == [
            _gdn("database-experts"),
            _gdn("backend-team"),
            _gdn("engineering-all"),
            _gdn("all-staff"),
        ]

        assert len(rows) == 4


class TestEffectiveMembershipsDiamond:
    def test_effective_memberships_diamond_pattern(
        self, test_directory: Directory, session: Session
    ) -> None:
        """carlos.garcia is reachable through two paths to all-staff.

        Variante B: we store one row per distinct path, so carlos
        appears twice for all-staff — once via engineering (depth 3)
        and once via marketing (depth 1). This preserves the audit trail.
        """
        sync_directory(test_directory.id)

        carlos_dn = _dn("carlos.garcia")
        rows = session.exec(
            select(EffectiveMembership).where(
                EffectiveMembership.directory_id == test_directory.id,
                EffectiveMembership.user_dn == carlos_dn,
            )
        ).all()

        # carlos has 6 effective membership rows:
        #   database-experts d=0, marketing-team d=0,
        #   backend-team d=1, all-staff d=1 (via marketing),
        #   engineering-all d=2, all-staff d=3 (via engineering)
        assert len(rows) == 6, (
            f"Expected 6 effective memberships for carlos (Variante B), got {len(rows)}. "
            f"Rows: {[(r.group_dn, r.depth, r.path) for r in rows]}"
        )

        # all-staff should appear exactly twice (two paths)
        all_staff_rows = [r for r in rows if r.group_dn == _gdn("all-staff")]
        assert len(all_staff_rows) == 2, (
            f"Expected 2 rows for all-staff (diamond), got {len(all_staff_rows)}"
        )
        all_staff_depths = sorted(r.depth for r in all_staff_rows)
        assert all_staff_depths == [1, 3], (
            f"all-staff depths should be [1, 3], got {all_staff_depths}"
        )

        # direct memberships (depth 0)
        direct = [r for r in rows if r.depth == 0]
        direct_groups = {r.group_dn for r in direct}
        assert direct_groups == {_gdn("database-experts"), _gdn("marketing-team")}


class TestEmptyGroup:
    def test_empty_group_has_no_memberships(
        self, test_directory: Directory, session: Session
    ) -> None:
        """empty-group should produce zero rows in effective_memberships."""
        sync_directory(test_directory.id)

        rows = session.exec(
            select(EffectiveMembership).where(
                EffectiveMembership.directory_id == test_directory.id,
                EffectiveMembership.group_dn == _gdn("empty-group"),
            )
        ).all()

        assert len(rows) == 0, (
            f"empty-group should have 0 effective memberships, got {len(rows)}"
        )


class TestMaterializationIdempotent:
    def test_materialization_is_idempotent(
        self, test_directory: Directory, session: Session
    ) -> None:
        """Running sync twice should not create duplicate membership rows."""
        sync_directory(test_directory.id)

        first_dm = len(
            session.exec(
                select(DirectMembership).where(
                    DirectMembership.directory_id == test_directory.id
                )
            ).all()
        )
        first_em = len(
            session.exec(
                select(EffectiveMembership).where(
                    EffectiveMembership.directory_id == test_directory.id
                )
            ).all()
        )

        sync_directory(test_directory.id)

        second_dm = len(
            session.exec(
                select(DirectMembership).where(
                    DirectMembership.directory_id == test_directory.id
                )
            ).all()
        )
        second_em = len(
            session.exec(
                select(EffectiveMembership).where(
                    EffectiveMembership.directory_id == test_directory.id
                )
            ).all()
        )

        assert first_dm == second_dm, (
            f"Direct memberships changed: {first_dm} → {second_dm}"
        )
        assert first_em == second_em, (
            f"Effective memberships changed: {first_em} → {second_em}"
        )


class TestUserMembershipsEndpoint:
    def test_user_memberships_endpoint_returns_sorted_by_depth(
        self, test_directory: Directory, session: Session, api_client
    ) -> None:
        """API response for alice.wong should sort direct first, inherited after."""
        sync_directory(test_directory.id)

        alice = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == test_directory.id,
                DirectoryUser.dn == _dn("alice.wong"),
            )
        ).first()
        assert alice is not None

        resp = api_client.get(
            f"/api/directories/{test_directory.id}/users/{alice.id}/memberships"
        )
        assert resp.status_code == 200, f"Unexpected status: {resp.status_code} — {resp.text}"

        data = resp.json()
        assert data["direct_count"] == 1
        assert data["inherited_count"] == 3
        assert data["total"] == 4

        depths = [m["depth"] for m in data["memberships"]]
        assert depths == sorted(depths), (
            f"Memberships should be sorted by depth ascending, got {depths}"
        )

        assert data["memberships"][0]["group_name"] == "database-experts"
        assert data["memberships"][0]["depth"] == 0


class TestGraphEndpointWithRootDn:
    def test_graph_endpoint_with_root_dn(
        self, test_directory: Directory, session: Session, api_client
    ) -> None:
        """Graph from engineering-all with depth=2 should include nested groups and users."""
        sync_directory(test_directory.id)

        resp = api_client.get(
            f"/api/directories/{test_directory.id}/graph",
            params={"root_dn": _gdn("engineering-all"), "depth": 2},
        )
        assert resp.status_code == 200, f"Unexpected status: {resp.status_code} — {resp.text}"

        data = resp.json()
        node_ids = {n["id"] for n in data["nodes"]}

        # Should include engineering-all, backend-team, database-experts (groups)
        assert _gdn("engineering-all") in node_ids
        assert _gdn("backend-team") in node_ids
        assert _gdn("database-experts") in node_ids

        # Should include users in database-experts and backend-team
        assert _dn("alice.wong") in node_ids
        assert _dn("carlos.garcia") in node_ids
        assert _dn("hannah.fischer") in node_ids

        # Should include all-staff as parent (upward traversal)
        assert _gdn("all-staff") in node_ids

        assert data["meta"]["edge_count"] > 0
        assert data["meta"]["truncated"] is False


class TestGraphEndpointDefaultView:
    def test_graph_endpoint_default_view(
        self, test_directory: Directory, session: Session, api_client
    ) -> None:
        """Default graph should return top groups by member count."""
        sync_directory(test_directory.id)

        resp = api_client.get(
            f"/api/directories/{test_directory.id}/graph"
        )
        assert resp.status_code == 200, f"Unexpected status: {resp.status_code} — {resp.text}"

        data = resp.json()
        assert data["meta"]["node_count"] > 0
        assert data["meta"]["edge_count"] > 0

        # flat-team has the most members (5), should be in the result
        node_ids = {n["id"] for n in data["nodes"]}
        assert _gdn("flat-team") in node_ids, (
            f"flat-team (most members) should be in default view, "
            f"got nodes: {node_ids}"
        )


class TestGraphEndpointTruncation:
    def test_graph_endpoint_truncation(
        self, test_directory: Directory, session: Session, api_client
    ) -> None:
        """With node_limit=5, should return exactly 5 nodes and meta.truncated=true."""
        sync_directory(test_directory.id)

        resp = api_client.get(
            f"/api/directories/{test_directory.id}/graph",
            params={"node_limit": 5},
        )
        assert resp.status_code == 200, f"Unexpected status: {resp.status_code} — {resp.text}"

        data = resp.json()
        assert data["meta"]["node_count"] == 5, (
            f"Expected exactly 5 nodes, got {data['meta']['node_count']}"
        )
        assert data["meta"]["truncated"] is True
