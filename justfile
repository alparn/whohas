default:
    @just --list

# Start the dev environment (postgres + backend)
dev:
    docker compose up -d postgres
    cd backend && uv run uvicorn app.main:app --reload

# Start the test LDAP
test-ldap-up:
    docker compose --profile test up test-ldap -d
    @echo "Test LDAP running at ldap://localhost:1389"
    @echo "Bind DN: cn=admin,dc=test,dc=local"
    @echo "Password: adminpassword"
    @echo "Base DN: dc=test,dc=local"

# Stop the test LDAP
test-ldap-down:
    docker compose --profile test down

# Inspect the test LDAP contents
test-ldap-inspect:
    docker compose exec test-ldap ldapsearch -x -H ldap://localhost:1389 -b "dc=test,dc=local" -D "cn=admin,dc=test,dc=local" -w adminpassword

# Run all tests
test:
    cd backend && uv run pytest

# Run only integration tests (requires test-ldap + postgres to be running)
test-integration:
    cd backend && uv run pytest -m integration -v

# Run only unit tests
test-unit:
    cd backend && uv run pytest -m "not integration"

# Open a psql shell into the dev database
db-shell:
    docker compose exec postgres psql -U lumen -d lumen

# Open a psql shell into the test database
db-shell-test:
    docker compose exec postgres psql -U lumen -d lumen_test

# Trigger a sync against a directory by ID
sync id:
    curl -s -X POST http://localhost:8000/api/directories/{{id}}/sync | python3 -m json.tool

# Check latest sync run for a directory
sync-status id:
    curl -s http://localhost:8000/api/directories/{{id}}/sync-runs/latest | python3 -m json.tool

# Tail backend logs
logs:
    docker compose logs -f backend

# Start the Samba AD test container
samba-ad-up:
    docker compose --profile test up test-samba-ad -d
    @echo "Samba AD running at ldap://localhost:2389"
    @echo "Bind DN: CN=Administrator,CN=Users,DC=test,DC=local"
    @echo "Password: Passw0rd"
    @echo "Base DN: DC=test,DC=local"

# Stop the Samba AD test container
samba-ad-down:
    docker compose --profile test stop test-samba-ad

# Inspect the Samba AD contents
samba-ad-inspect:
    docker compose exec test-samba-ad ldapsearch -x -H ldap://localhost:389 -b "DC=test,DC=local" -D "CN=Administrator,CN=Users,DC=test,DC=local" -w Passw0rd

# Run only Samba AD integration tests (requires test-samba-ad + postgres to be running)
test-ad:
    cd backend && uv run pytest -m samba_ad -v

# Run the full test setup from scratch
test-setup: test-ldap-up
    @echo "Waiting for LDAP healthcheck..."
    @sleep 10
    @echo "Test LDAP is ready. Run 'just test-integration' to execute tests."
