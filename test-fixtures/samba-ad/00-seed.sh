#!/bin/sh
# =============================================================================
# whohas Samba AD Test Seed Data
# =============================================================================
#
# Runs inside the smblds/smblds container via /entrypoint.d before the
# daemon starts.  Uses `samba-tool` to create real AD objects so the
# integration tests exercise native AD attributes:
#   - objectClass=user / objectClass=group
#   - sAMAccountName, mail, displayName
#   - userAccountControl (514 = disabled)
#   - lastLogon (Windows FILETIME)
#   - groupType (-2147483646 = security global)
#   - member (group nesting)
#
# Structure (mirrors OpenLDAP seed for test parity):
#   DC=test,DC=local
#   └── CN=Users          (Samba default container)
#       ├── 15 user accounts
#       │   ├── 10 normal active users
#       │   ├── 2 disabled users (samba-tool user disable)
#       │   ├── 1 special chars user (Björn Müller-Schäfer)
#       │   ├── 1 user with no email
#       │   └── 1 duplicate display name (same as john.doe)
#       └── 8 groups
#           ├── flat-team               — 5 direct user members
#           ├── empty-group             — 0 members
#           ├── database-experts        — 2 users (leaf of nested chain)
#           ├── backend-team            — database-experts + 1 user
#           ├── engineering-all         — backend-team
#           ├── marketing-team          — 2 users (one shared = diamond)
#           ├── all-staff               — engineering-all + marketing-team
#           └── single-user-group       — 1 user
# =============================================================================

set -eu

DOMAIN_DN="DC=test,DC=local"
USERS_DN="CN=Users,${DOMAIN_DN}"
DEFAULT_PASS="Passw0rd"

# ---- helper ----------------------------------------------------------------

create_user() {
    local sam="$1"
    local given="$2"
    local surname="$3"
    local display="$4"
    local mail="${5:-}"

    local mail_opt=""
    if [ -n "$mail" ]; then
        mail_opt="--mail-address=${mail}"
    fi

    samba-tool user create "$sam" "$DEFAULT_PASS" \
        --given-name="$given" \
        --surname="$surname" \
        $mail_opt
}

set_last_logon() {
    local cn="$1"
    local filetime="$2"
    local user_dn="CN=${cn},${USERS_DN}"

    ldbmodify -H /var/lib/samba/private/sam.ldb <<EOF
dn: ${user_dn}
changetype: modify
replace: lastLogon
lastLogon: ${filetime}
EOF
}

set_display_name() {
    local cn="$1"
    local display="$2"
    local user_dn="CN=${cn},${USERS_DN}"

    ldbmodify -H /var/lib/samba/private/sam.ldb <<EOF
dn: ${user_dn}
changetype: modify
replace: displayName
displayName: ${display}
EOF
}

# ---- Users (15 total) ------------------------------------------------------

# 1–10: Normal active users
create_user "john.doe"       "John"    "Doe"       "John Doe"               "john.doe@test.local"
create_user "jane.smith"     "Jane"    "Smith"     "Jane Smith"             "jane.smith@test.local"
create_user "alice.wong"     "Alice"   "Wong"      "Alice Wong"             "alice.wong@test.local"
create_user "carlos.garcia"  "Carlos"  "Garcia"    "Carlos Garcia"          "carlos.garcia@test.local"
create_user "diana.ross"     "Diana"   "Ross"      "Diana Ross"             "diana.ross@test.local"
create_user "erik.larsson"   "Erik"    "Larsson"   "Erik Larsson"           "erik.larsson@test.local"
create_user "fatima.khan"    "Fatima"  "Khan"      "Fatima Khan"            "fatima.khan@test.local"
create_user "george.chen"    "George"  "Chen"      "George Chen"            "george.chen@test.local"
create_user "hannah.fischer" "Hannah"  "Fischer"   "Hannah Fischer"         "hannah.fischer@test.local"
create_user "ivan.petrov"    "Ivan"    "Petrov"    "Ivan Petrov"            "ivan.petrov@test.local"

# 11–12: Disabled users (created active, then disabled via samba-tool)
create_user "disabled.user1" "Disabled" "One"      "Disabled User One"      "disabled1@test.local"
create_user "disabled.user2" "Disabled" "Two"      "Disabled User Two"      "disabled2@test.local"

samba-tool user disable disabled.user1
samba-tool user disable disabled.user2

# 13: Special characters (umlauts)
create_user "bjoern.mueller" "Björn"   "Müller-Schäfer" "Björn Müller-Schäfer" "bjoern.mueller@test.local"

# 14: User with NO email
create_user "noemail.user"   "NoEmail" "User"      "NoEmail User"

# 15: Duplicate display name (same displayName as john.doe)
#     CN must be unique in AD, so create with a distinct surname, then override displayName
create_user "john.doe2"      "John"    "Doe II"    "John Doe II"            "john.doe2@test.local"
set_display_name "John Doe II" "John Doe"

# ---- AD-specific: lastLogon timestamps (Windows FILETIME) ------------------
# FILETIME = 100-ns ticks since 1601-01-01 00:00:00 UTC
# 2024-01-15 09:30:00 UTC = 133500078000000000
# 2023-06-01 14:00:00 UTC = 133300440000000000
# 0 = never logged on

set_last_logon "John Doe"          "133500078000000000"
set_last_logon "Jane Smith"        "133300440000000000"
set_last_logon "Alice Wong"        "133500078000000000"
set_last_logon "Disabled One"      "0"
set_last_logon "Disabled Two"      "0"

# ---- Groups (8 total) ------------------------------------------------------

samba-tool group add flat-team
samba-tool group add empty-group
samba-tool group add database-experts
samba-tool group add backend-team
samba-tool group add engineering-all
samba-tool group add marketing-team
samba-tool group add all-staff
samba-tool group add single-user-group

# ---- Group memberships -----------------------------------------------------

# flat-team: 5 direct user members
samba-tool group addmembers flat-team john.doe,jane.smith,erik.larsson,fatima.khan,george.chen

# database-experts: 2 users (leaf of nested chain)
samba-tool group addmembers database-experts alice.wong,carlos.garcia

# backend-team: database-experts (nested group) + 1 user
samba-tool group addmembers backend-team database-experts,hannah.fischer

# engineering-all: backend-team (nested group)
samba-tool group addmembers engineering-all backend-team

# marketing-team: 2 users (carlos.garcia shared with database-experts = diamond)
samba-tool group addmembers marketing-team carlos.garcia,diana.ross

# all-staff: engineering-all + marketing-team (diamond root)
samba-tool group addmembers all-staff engineering-all,marketing-team

# single-user-group: 1 user
samba-tool group addmembers single-user-group ivan.petrov

# empty-group: intentionally left with no members

echo "=== Samba AD seed complete: 15 users, 8 groups ==="
