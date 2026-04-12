# whohas

Identity intelligence for your LDAP and Active Directory — see who has access to what, find stale accounts, audit group memberships.

[![License: AGPL-3.0](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![GHCR](https://img.shields.io/badge/GHCR-packages-blue?logo=github)](https://github.com/alparn/whohas/pkgs)
[![Release](https://img.shields.io/github/v/release/alparn/whohas)](https://github.com/alparn/whohas/releases)

![Dashboard](screens/dashboard.png)
*The dashboard — see your directory's health at a glance.*

**Why whohas?**

- See effective group memberships including nested groups — something most directory tools get wrong
- Find stale accounts, empty groups, and permission creep without writing custom scripts
- Self-hosted, open-source, read-only by design — your directory data never leaves your infrastructure

![User detail](screens/user-details.png)
*Effective group memberships, showing direct and inherited paths through nested groups.*

## Quickstart

```bash
git clone https://github.com/alparn/whohas.git
cd whohas
cp .env.example .env
docker compose up -d
```

Open http://localhost:3000 and add your first directory.

## Features

- Directory sync for OpenLDAP, Active Directory, and any RFC-compliant LDAP server
- Cached snapshots in Postgres — fast search without hammering the LDAP server
- Full-text search across users and groups with typo tolerance
- Effective group memberships with path visualization
- Insights dashboard: stale accounts, empty groups, largest groups, disabled users still in groups
- REST API with automatic OpenAPI documentation

## Status

Early-stage read-only MVP. Write operations (password reset, group management), delta sync, and more analytics are on the roadmap. Feedback and contributions welcome.

## Configuration

All configuration is done through environment variables. See [`.env.example`](.env.example) for the full list with comments. The defaults work for local development — the only required variable in production is `SECRET_KEY`.

## Development

**Prerequisites:** Docker, Python 3.12+, Node 22+, [uv](https://docs.astral.sh/uv/), [just](https://github.com/casey/just)

```bash
just dev          # starts Postgres + backend
cd frontend && npm run dev   # starts frontend
```

See [TESTING.md](TESTING.md) for running the test suite.

## Using published images

For users who want to run whohas without cloning the repo:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: whohas
      POSTGRES_PASSWORD: whohas
      POSTGRES_DB: whohas
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    image: ghcr.io/alparn/whohas-backend:latest
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: "postgresql+psycopg://whohas:whohas@postgres:5432/whohas"
      SECRET_KEY: "change-me-in-production"
    depends_on:
      - postgres

  frontend:
    image: ghcr.io/alparn/whohas-frontend:latest
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: "http://backend:8000"
    depends_on:
      - backend

volumes:
  pgdata:
```

## License

AGPL-3.0. See [LICENSE](LICENSE).
