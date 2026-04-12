from __future__ import annotations

import time

import pytest
from sqlmodel import Session, select

from app.models.directory import Directory
from app.models.group import DirectoryGroup
from app.models.membership import EffectiveMembership
from app.models.sync_run import SyncRun, SyncStatus
from app.models.user import DirectoryUser
from app.services.sync import sync_directory

pytestmark = [pytest.mark.integration, pytest.mark.samba_ad]


def _run_sync(directory: Directory) -> None:
    sync_directory(directory.id)


class TestSyncCreatesUsersFromAD:
    def test_sync_creates_users_from_ad(
        self, test_directory_ad: Directory, session: Session
    ) -> None:
        """All 15 seed users are synced and sAMAccountName is populated (not uid fallback)."""
        _run_sync(test_directory_ad)

        users = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == test_directory_ad.id
            )
        ).all()

        run = session.exec(
            select(SyncRun).where(SyncRun.directory_id == test_directory_ad.id)
        ).first()
        assert run is not None and run.status == SyncStatus.SUCCESS, (
            f"Sync did not succeed. Status={run.status if run else 'None'}, "
            f"Error={run.error_message if run else 'no run'}"
        )

        assert len(users) == 15, (
            f"Expected 15 users from Samba AD, got {len(users)}. "
            f"DNs: {[u.dn for u in users]}"
        )

        expected_sams = {
            "john.doe", "jane.smith", "alice.wong", "carlos.garcia",
            "diana.ross", "erik.larsson", "fatima.khan", "george.chen",
            "hannah.fischer", "ivan.petrov", "disabled.user1",
            "disabled.user2", "bjoern.mueller", "noemail.user", "john.doe2",
        }
        actual_sams = {u.sam_account_name for u in users}
        assert actual_sams == expected_sams, (
            f"sAMAccountName mismatch.\n"
            f"  Missing: {expected_sams - actual_sams}\n"
            f"  Extra:   {actual_sams - expected_sams}"
        )

        for user in users:
            assert user.sam_account_name, (
                f"User {user.dn} has empty sam_account_name — "
                f"sAMAccountName should be populated for AD users, not uid fallback"
            )


class TestSyncDetectsDisabledViaUAC:
    def test_sync_detects_disabled_via_uac(
        self, test_directory_ad: Directory, session: Session
    ) -> None:
        """The 2 disabled users are detected via userAccountControl flag (not description hack)."""
        _run_sync(test_directory_ad)

        users = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == test_directory_ad.id
            )
        ).all()

        disabled_users = [u for u in users if u.account_disabled]
        disabled_sams = {u.sam_account_name for u in disabled_users}

        assert len(disabled_users) == 2, (
            f"Expected exactly 2 disabled users via userAccountControl, "
            f"got {len(disabled_users)}: {disabled_sams}"
        )
        assert disabled_sams == {"disabled.user1", "disabled.user2"}, (
            f"Wrong disabled users. Expected disabled.user1 and disabled.user2, "
            f"got {disabled_sams}"
        )

        enabled_users = [u for u in users if not u.account_disabled]
        assert len(enabled_users) == 13, (
            f"Expected 13 enabled users, got {len(enabled_users)}"
        )


class TestSyncParsesADLastLogon:
    def test_sync_parses_ad_last_logon(
        self, test_directory_ad: Directory, session: Session
    ) -> None:
        """Users with lastLogon timestamps have real datetime values parsed from AD FILETIME."""
        _run_sync(test_directory_ad)

        users = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == test_directory_ad.id
            )
        ).all()

        users_with_logon = [u for u in users if u.last_logon is not None]
        assert len(users_with_logon) >= 1, (
            "Expected at least 1 user with a parsed last_logon timestamp, got 0. "
            "Seed sets lastLogon on john.doe, jane.smith, and alice.wong."
        )

        john = next(
            (u for u in users if u.sam_account_name == "john.doe"), None
        )
        assert john is not None, "john.doe not found"
        assert john.last_logon is not None, (
            "john.doe should have last_logon parsed from FILETIME 133500078000000000"
        )
        assert john.last_logon.year == 2024, (
            f"john.doe last_logon year should be 2024, got {john.last_logon.year}"
        )
        assert john.last_logon.month == 1, (
            f"john.doe last_logon month should be 1, got {john.last_logon.month}"
        )

        jane = next(
            (u for u in users if u.sam_account_name == "jane.smith"), None
        )
        assert jane is not None, "jane.smith not found"
        assert jane.last_logon is not None, (
            "jane.smith should have last_logon parsed from FILETIME 133300440000000000"
        )
        assert jane.last_logon.year == 2023, (
            f"jane.smith last_logon year should be 2023, got {jane.last_logon.year}"
        )

        disabled1 = next(
            (u for u in users if u.sam_account_name == "disabled.user1"), None
        )
        assert disabled1 is not None, "disabled.user1 not found"
        assert disabled1.last_logon is None, (
            "disabled.user1 had lastLogon=0 which should parse to None"
        )


class TestMembershipsWithADGroups:
    def test_memberships_work_with_ad_groups(
        self, test_directory_ad: Directory, session: Session
    ) -> None:
        """Nesting and effective memberships resolve correctly through AD groups."""
        _run_sync(test_directory_ad)

        groups = session.exec(
            select(DirectoryGroup).where(
                DirectoryGroup.directory_id == test_directory_ad.id
            )
        ).all()
        group_names = {g.name for g in groups}
        assert len(groups) == 8, (
            f"Expected 8 groups, got {len(groups)}: {group_names}"
        )

        effective = session.exec(
            select(EffectiveMembership).where(
                EffectiveMembership.directory_id == test_directory_ad.id
            )
        ).all()
        assert len(effective) > 0, (
            "No effective memberships materialized — recursive CTE should "
            "have produced rows from the AD group nesting."
        )

        all_staff_dn = next(
            (g.dn for g in groups if g.name == "all-staff"), None
        )
        assert all_staff_dn is not None, "all-staff group not found"

        all_staff_members = {
            e.user_dn for e in effective if e.group_dn == all_staff_dn
        }
        assert len(all_staff_members) >= 4, (
            f"all-staff should have at least 4 effective user members "
            f"(via engineering-all -> backend-team -> database-experts + marketing-team), "
            f"got {len(all_staff_members)}: {all_staff_members}"
        )

        engineering_dn = next(
            (g.dn for g in groups if g.name == "engineering-all"), None
        )
        assert engineering_dn is not None, "engineering-all group not found"

        eng_members = {
            e.user_dn for e in effective if e.group_dn == engineering_dn
        }
        assert len(eng_members) >= 3, (
            f"engineering-all should have at least 3 effective members "
            f"(alice.wong, carlos.garcia from database-experts + hannah.fischer from backend-team), "
            f"got {len(eng_members)}"
        )

        deep_rows = [
            e for e in effective
            if e.group_dn == all_staff_dn and e.depth >= 2
        ]
        assert len(deep_rows) > 0, (
            "Expected effective memberships at depth >= 2 in all-staff "
            "(all-staff -> engineering-all -> backend-team -> database-experts)"
        )


class TestInsightsDisabledInGroupsAD:
    def test_insights_disabled_in_groups_ad(
        self, test_directory_ad: Directory, session: Session, api_client
    ) -> None:
        """Disabled users with group memberships appear in the insights endpoint."""
        _run_sync(test_directory_ad)

        response = api_client.get(
            f"/api/directories/{test_directory_ad.id}/insights/disabled-in-groups",
            params={"limit": 50},
        )

        assert response.status_code == 200, (
            f"Insights endpoint returned {response.status_code}: {response.text}"
        )

        results = response.json()

        disabled_users = session.exec(
            select(DirectoryUser).where(
                DirectoryUser.directory_id == test_directory_ad.id,
                DirectoryUser.account_disabled == True,  # noqa: E712
            )
        ).all()
        disabled_dns = {u.dn for u in disabled_users}

        effective = session.exec(
            select(EffectiveMembership).where(
                EffectiveMembership.directory_id == test_directory_ad.id
            )
        ).all()
        disabled_with_memberships = {
            e.user_dn for e in effective if e.user_dn in disabled_dns
        }

        if disabled_with_memberships:
            assert len(results) >= 1, (
                f"There are {len(disabled_with_memberships)} disabled users "
                f"with group memberships, but the insights endpoint returned 0 results. "
                f"Disabled DNs with memberships: {disabled_with_memberships}"
            )
            result_dns = {r.get("dn") for r in results}
            for dn in disabled_with_memberships:
                assert dn in result_dns, (
                    f"Disabled user {dn} has group memberships but is missing "
                    f"from the insights/disabled-in-groups response"
                )
        else:
            assert len(results) == 0, (
                "No disabled users have memberships in the seed data, "
                "so the endpoint should return an empty list"
            )
