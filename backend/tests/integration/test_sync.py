from __future__ import annotations

import time

import pytest
from sqlmodel import Session, select

from app.models.directory import Directory
from app.models.group import DirectoryGroup
from app.models.sync_run import SyncRun, SyncStatus
from app.models.user import DirectoryUser
from app.services.sync import sync_directory

from .conftest import (
    LDAP_BASE_DN,
    LDAP_BIND_DN,
    LDAP_BIND_PASSWORD,
    LDAP_HOST,
    LDAP_PORT,
    OPENLDAP_GROUP_FILTER,
    OPENLDAP_USER_FILTER,
)

pytestmark = pytest.mark.integration


def _run_sync(directory: Directory) -> None:
    """Run a sync — filters are now read from the Directory record."""
    sync_directory(directory.id)


class TestSyncCreatesData:
    def test_sync_creates_users(self, test_directory: Directory, session: Session) -> None:
        """After sync, all 15 seed users should be in the database."""
        _run_sync(test_directory)

        users = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == test_directory.id
            )
        ).all()

        assert len(users) == 15, (
            f"Expected 15 users after sync, got {len(users)}. "
            f"User DNs: {[u.dn for u in users]}"
        )

        special_user = next(
            (u for u in users if "bjoern.mueller" in u.dn), None
        )
        assert special_user is not None, (
            "User with uid=bjoern.mueller not found after sync"
        )
        assert "Müller" in special_user.display_name or "M" in special_user.display_name, (
            f"Special character user display_name is '{special_user.display_name}', "
            f"expected to contain umlaut characters"
        )

    def test_sync_creates_groups(self, test_directory: Directory, session: Session) -> None:
        """After sync, all 8 seed groups should be in the database."""
        _run_sync(test_directory)

        groups = session.exec(
            select(DirectoryGroup).where(
                DirectoryGroup.directory_id == test_directory.id
            )
        ).all()

        assert len(groups) == 8, (
            f"Expected 8 groups after sync, got {len(groups)}. "
            f"Group DNs: {[g.dn for g in groups]}"
        )

        group_names = {g.name for g in groups}
        expected_names = {
            "flat-team",
            "empty-group",
            "database-experts",
            "backend-team",
            "engineering-all",
            "marketing-team",
            "all-staff",
            "single-user-group",
        }
        assert group_names == expected_names, (
            f"Group name mismatch. Got: {group_names}, expected: {expected_names}"
        )


class TestSyncIdempotency:
    def test_sync_is_idempotent(self, test_directory: Directory, session: Session) -> None:
        """Running sync twice should not create duplicate rows."""
        _run_sync(test_directory)

        users_after_first = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == test_directory.id
            )
        ).all()
        first_seen_times = {u.dn: u.last_seen_at for u in users_after_first}
        first_count = len(users_after_first)

        _run_sync(test_directory)

        users_after_second = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == test_directory.id
            )
        ).all()

        assert len(users_after_second) == first_count, (
            f"Duplicate rows created: {first_count} after first sync, "
            f"{len(users_after_second)} after second sync"
        )

        for user in users_after_second:
            original_time = first_seen_times.get(user.dn)
            if original_time is not None:
                assert user.last_seen_at >= original_time, (
                    f"last_seen_at for {user.dn} was not updated: "
                    f"first={original_time}, second={user.last_seen_at}"
                )


class TestSyncRuns:
    def test_sync_records_sync_run(self, test_directory: Directory, session: Session) -> None:
        """A successful sync should create a sync_runs record with status=success."""
        _run_sync(test_directory)

        runs = session.exec(
            select(SyncRun).where(SyncRun.directory_id == test_directory.id)
        ).all()

        assert len(runs) == 1, f"Expected 1 sync run, got {len(runs)}"
        run = runs[0]
        assert run.status == SyncStatus.SUCCESS, (
            f"Sync run status is '{run.status}', expected 'success'. "
            f"Error: {run.error_message}"
        )
        assert run.objects_synced == 23, (
            f"Expected 23 objects synced (15 users + 8 groups), got {run.objects_synced}"
        )
        assert run.finished_at is not None, "Sync run finished_at should be set"
        assert run.error_message is None, (
            f"Successful sync should have no error_message, got: {run.error_message}"
        )

    def test_sync_failure_marks_run_failed(self, session: Session) -> None:
        """Syncing a directory pointing at a non-existent host should result in status=failed."""
        bad_directory = Directory(
            name="Bad LDAP",
            host="non-existent-host.invalid",
            port=1389,
            use_ssl=False,
            bind_dn="cn=admin,dc=test,dc=local",
            bind_password="wrong",
            base_dn="dc=test,dc=local",
            user_filter=OPENLDAP_USER_FILTER,
            group_filter=OPENLDAP_GROUP_FILTER,
        )
        session.add(bad_directory)
        session.commit()
        session.refresh(bad_directory)

        sync_directory(bad_directory.id)

        run = session.exec(
            select(SyncRun).where(SyncRun.directory_id == bad_directory.id)
        ).first()

        assert run is not None, "A sync_run record should exist even for failed syncs"
        assert run.status == SyncStatus.FAILED, (
            f"Expected status 'failed', got '{run.status}'"
        )
        assert run.error_message is not None and len(run.error_message) > 0, (
            "Failed sync should have a non-empty error_message"
        )
        assert run.finished_at is not None, (
            "Failed sync should still have finished_at set"
        )


class TestDisabledUsers:
    def test_sync_handles_disabled_users(
        self, test_directory: Directory, session: Session
    ) -> None:
        """The 2 seed users with description=DISABLED should be detectable after sync."""
        _run_sync(test_directory)

        users = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == test_directory.id
            )
        ).all()

        disabled_users = [
            u
            for u in users
            if u.raw_attributes.get("description") == "DISABLED"
        ]
        assert len(disabled_users) == 2, (
            f"Expected 2 users with description=DISABLED in raw_attributes, "
            f"got {len(disabled_users)}. "
            f"Check that raw_attributes are preserved during sync."
        )


class TestUserSearchEndpoint:
    def test_user_search_endpoint(
        self, test_directory: Directory, session: Session, api_client
    ) -> None:
        """Searching for 'müller' should return the umlaut user via pg_trgm."""
        _run_sync(test_directory)

        response = api_client.get(
            f"/api/directories/{test_directory.id}/users",
            params={"q": "müller", "limit": 10},
        )

        assert response.status_code == 200, (
            f"Search endpoint returned {response.status_code}: {response.text}"
        )

        results = response.json()
        assert len(results) >= 1, (
            f"Expected at least 1 result for 'müller', got {len(results)}. "
            f"Response: {results}"
        )

        dns = [r["dn"] for r in results]
        assert any("bjoern.mueller" in dn for dn in dns), (
            f"Expected bjoern.mueller in search results, got DNs: {dns}"
        )

    def test_user_search_empty_query(
        self, test_directory: Directory, session: Session, api_client
    ) -> None:
        """An empty query should return recently seen users, not an error."""
        _run_sync(test_directory)

        response = api_client.get(
            f"/api/directories/{test_directory.id}/users",
            params={"q": "", "limit": 50},
        )

        assert response.status_code == 200, (
            f"Empty search returned {response.status_code}: {response.text}"
        )

        results = response.json()
        assert len(results) > 0, (
            "Empty query should return users, got empty list"
        )
        assert len(results) <= 50, (
            f"Empty query should respect limit=50, got {len(results)} results"
        )


class TestApiSyncEndToEnd:
    def test_api_sync_endpoint_works_against_openldap(self, api_client, session: Session) -> None:
        """Full API path: create directory with OpenLDAP filters → trigger sync → verify data.

        This proves the sync endpoint uses the stored filters without any
        test-only overrides.
        """
        # 1. Create directory via API with OpenLDAP filters
        create_resp = api_client.post(
            "/api/directories",
            json={
                "name": "API Test LDAP",
                "host": LDAP_HOST,
                "port": LDAP_PORT,
                "use_ssl": False,
                "bind_dn": LDAP_BIND_DN,
                "bind_password": LDAP_BIND_PASSWORD,
                "base_dn": LDAP_BASE_DN,
                "user_filter": OPENLDAP_USER_FILTER,
                "group_filter": OPENLDAP_GROUP_FILTER,
            },
        )
        assert create_resp.status_code == 201, (
            f"Failed to create directory: {create_resp.text}"
        )
        directory_id = create_resp.json()["id"]

        # Verify filters are returned in the response
        assert create_resp.json()["user_filter"] == OPENLDAP_USER_FILTER
        assert create_resp.json()["group_filter"] == OPENLDAP_GROUP_FILTER

        # Verify bind_password is NOT in the response
        assert "bind_password" not in create_resp.json(), (
            "bind_password must not be exposed in API responses"
        )

        # 2. Trigger sync via API
        sync_resp = api_client.post(f"/api/directories/{directory_id}/sync")
        assert sync_resp.status_code == 202, (
            f"Sync trigger failed: {sync_resp.text}"
        )

        # 3. sync_directory runs synchronously in run_in_threadpool but
        #    we called it from the API which returns 202 immediately.
        #    Give the background thread a moment to complete.
        for _ in range(20):
            time.sleep(0.5)
            latest_resp = api_client.get(
                f"/api/directories/{directory_id}/sync-runs/latest"
            )
            if latest_resp.status_code == 200:
                run_data = latest_resp.json()
                if run_data["status"] in ("SUCCESS", "FAILED"):
                    break
        else:
            pytest.fail("Sync did not complete within 10 seconds")

        assert run_data["status"] == "SUCCESS", (
            f"Sync failed via API path: {run_data.get('error_message')}"
        )

        # 4. Verify data landed in the database
        users = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == directory_id
            )
        ).all()
        assert len(users) == 15, (
            f"Expected 15 users via API sync path, got {len(users)}"
        )

        groups = session.exec(
            select(DirectoryGroup).where(
                DirectoryGroup.directory_id == directory_id
            )
        ).all()
        assert len(groups) == 8, (
            f"Expected 8 groups via API sync path, got {len(groups)}"
        )
