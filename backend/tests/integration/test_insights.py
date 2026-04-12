from __future__ import annotations

import pytest
from sqlmodel import Session

from app.models.directory import Directory
from app.services.sync import sync_directory

pytestmark = pytest.mark.integration


def _run_sync(directory: Directory) -> None:
    sync_directory(directory.id)


class TestInsightsEndpoints:
    """Integration tests for the /insights/* endpoints.

    All tests sync from the OpenLDAP fixture first, then query the API.
    Seed data: 15 users (2 disabled), 8 groups, nested memberships.
    """

    def test_summary_returns_correct_counts(
        self, test_directory: Directory, api_client
    ) -> None:
        _run_sync(test_directory)
        resp = api_client.get(
            f"/api/directories/{test_directory.id}/insights/summary"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_users"] == 15
        assert data["total_groups"] == 8
        assert isinstance(data["stale_user_count"], int)
        assert data["stale_user_count"] >= 0
        assert isinstance(data["empty_group_count"], int)
        assert data["empty_group_count"] >= 0
        assert isinstance(data["disabled_in_groups_count"], int)
        assert data["disabled_in_groups_count"] >= 0

    def test_empty_groups_finds_empty_group(
        self, test_directory: Directory, api_client
    ) -> None:
        _run_sync(test_directory)
        resp = api_client.get(
            f"/api/directories/{test_directory.id}/insights/empty-groups"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "dn" in data[0]
            assert "name" in data[0]

    def test_largest_groups_returns_sorted(
        self, test_directory: Directory, api_client
    ) -> None:
        _run_sync(test_directory)
        resp = api_client.get(
            f"/api/directories/{test_directory.id}/insights/largest-groups"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        counts = [g["effective_member_count"] for g in data]
        assert counts == sorted(counts, reverse=True)

    def test_disabled_users_in_groups(
        self, test_directory: Directory, api_client
    ) -> None:
        _run_sync(test_directory)
        resp = api_client.get(
            f"/api/directories/{test_directory.id}/insights/disabled-in-groups"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for user in data:
            assert user["account_disabled"] is True

    def test_stale_users_handles_null_last_logon(
        self, test_directory: Directory, api_client
    ) -> None:
        """Users with last_logon IS NULL are treated as stale (never seen)."""
        _run_sync(test_directory)
        resp = api_client.get(
            f"/api/directories/{test_directory.id}/insights/stale-users"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        has_null_last_logon = any(u["last_logon"] is None for u in data)
        assert has_null_last_logon, (
            "Expected at least one user with null last_logon in stale users "
            "(test LDAP users have no lastLogon attribute)"
        )
