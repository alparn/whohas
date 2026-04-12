# Testing Guide

## Prerequisites

- Docker Compose
- Python 3.12+ with [uv](https://docs.astral.sh/uv/)
- Postgres running (`docker compose up -d postgres`)

## Start the Test LDAP

```bash
just test-ldap-up
# or manually:
docker compose --profile test up test-ldap -d
```

Wait ~10 seconds for the healthcheck to pass and LDIF data to load.

## Test LDAP Credentials

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `1389` |
| Bind DN | `cn=admin,dc=test,dc=local` |
| Password | `adminpassword` |
| Base DN | `dc=test,dc=local` |

## Seed Data Structure

**15 Users** in `ou=people,dc=test,dc=local`:

| uid | Notes |
|---|---|
| john.doe | Normal (duplicate display name with john.doe2) |
| jane.smith | Normal |
| alice.wong | In database-experts group |
| carlos.garcia | Diamond pattern — in database-experts AND marketing-team |
| diana.ross | In marketing-team |
| erik.larsson | In flat-team |
| fatima.khan | In flat-team |
| george.chen | In flat-team |
| hannah.fischer | In backend-team |
| ivan.petrov | In single-user-group |
| disabled.user1 | `description: DISABLED` |
| disabled.user2 | `description: DISABLED` |
| bjoern.mueller | Display name: Björn Müller-Schäfer (umlauts) |
| noemail.user | No email attribute |
| john.doe2 | Same display name as john.doe |

**8 Groups** in `ou=groups,dc=test,dc=local`:

| cn | Members | Notes |
|---|---|---|
| flat-team | 5 direct users | No nesting |
| empty-group | self-referencing | For stale detection |
| database-experts | alice.wong, carlos.garcia | Leaf of nesting chain |
| backend-team | database-experts, hannah.fischer | Nested group + user |
| engineering-all | backend-team | Contains nested chain |
| marketing-team | carlos.garcia, diana.ross | Shares member with engineering |
| all-staff | engineering-all, marketing-team | Diamond pattern root |
| single-user-group | ivan.petrov | Permission isolation |

## Inspect LDAP Contents

```bash
just test-ldap-inspect
```

## Manual Testing Against the API

```bash
# 1. Create a directory pointing at the test LDAP
curl -s -X POST http://localhost:8000/api/directories \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test LDAP",
    "host": "localhost",
    "port": 1389,
    "use_ssl": false,
    "bind_dn": "cn=admin,dc=test,dc=local",
    "bind_password": "adminpassword",
    "base_dn": "dc=test,dc=local"
  }' | python3 -m json.tool

# 2. Copy the directory ID from the response, then trigger a sync
just sync <directory-id>

# 3. Check the sync result
just sync-status <directory-id>

# 4. Search users
curl -s "http://localhost:8000/api/directories/<directory-id>/users?q=john" | python3 -m json.tool
```

## Run Integration Tests

```bash
# Requires postgres + test-ldap to be running
just test-integration

# Run all tests (integration will be skipped if LDAP isn't up)
just test
```

## Common Gotchas

- **Sync returns 0 users**: Check that the LDAP healthcheck is green (`docker compose --profile test ps`). LDIF loading takes a few seconds after container start.
- **Connection refused on port 1389**: The test LDAP is behind the `test` Compose profile. Use `docker compose --profile test up test-ldap -d`.
- **Test DB errors**: Tests use `lumen_test` database. It's created automatically, but Postgres must be running.
- **OpenLDAP vs AD**: Tests use `(objectClass=inetOrgPerson)` instead of `(objectClass=user)`. The `sAMAccountName` field maps to `uid` in OpenLDAP — the sync stores `uid` in `sam_account_name`. This is expected.
