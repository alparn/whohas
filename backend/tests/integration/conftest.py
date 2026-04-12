from __future__ import annotations

import os
from collections.abc import Generator

import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

TEST_DB_NAME = "lumen_test"
PG_PORT = os.environ.get("PG_TEST_PORT", "5433")
TEST_DB_URL = f"postgresql+psycopg://lumen:lumen@localhost:{PG_PORT}/{TEST_DB_NAME}"
RAW_TEST_DB_URL = f"postgresql://lumen:lumen@localhost:{PG_PORT}/{TEST_DB_NAME}"

LDAP_HOST = "localhost"
LDAP_PORT = 1389
LDAP_BIND_DN = "cn=admin,dc=test,dc=local"
LDAP_BIND_PASSWORD = "adminpassword"
LDAP_BASE_DN = "dc=test,dc=local"

OPENLDAP_USER_FILTER = "(objectClass=inetOrgPerson)"
OPENLDAP_GROUP_FILTER = "(objectClass=groupOfNames)"

SAMBA_AD_HOST = "localhost"
SAMBA_AD_PORT = 2389
SAMBA_AD_BIND_DN = "CN=Administrator,CN=Users,DC=test,DC=local"
SAMBA_AD_BIND_PASSWORD = "Passw0rd"
SAMBA_AD_BASE_DN = "DC=test,DC=local"
SAMBA_AD_USER_FILTER = "(&(objectClass=user)(objectCategory=person)(!(isCriticalSystemObject=TRUE)))"
SAMBA_AD_GROUP_FILTER = "(&(objectClass=group)(!(isCriticalSystemObject=TRUE))(!(adminCount=1))(!(cn=Dns*)))"


def _create_test_db() -> None:
    raw_admin = f"postgresql://lumen:lumen@localhost:{PG_PORT}/postgres"
    with psycopg.connect(raw_admin, autocommit=True) as conn:
        exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", [TEST_DB_NAME]
        ).fetchone()
        if not exists:
            conn.execute(f"CREATE DATABASE {TEST_DB_NAME}")


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database and engine for the entire test session."""
    _create_test_db()

    with psycopg.connect(RAW_TEST_DB_URL, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    engine = create_engine(TEST_DB_URL, echo=False)

    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _patch_engine(test_engine, monkeypatch):
    """Patch the sync module's engine to use the test DB for ALL tests."""
    import app.db
    import app.services.sync

    monkeypatch.setattr(app.db, "engine", test_engine)
    monkeypatch.setattr(app.services.sync, "engine", test_engine)


@pytest.fixture(autouse=True)
def _clean_tables(test_engine):
    """Truncate all tables before each test for isolation."""
    with Session(test_engine) as session:
        for table in reversed(SQLModel.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    yield


@pytest.fixture()
def session(test_engine) -> Generator[Session, None, None]:
    with Session(test_engine) as session:
        yield session


@pytest.fixture()
def test_directory(session: Session):
    """Create a Directory record pointing at the local test LDAP."""
    from app.models.directory import Directory

    directory = Directory(
        name="Test LDAP",
        host=LDAP_HOST,
        port=LDAP_PORT,
        use_ssl=False,
        bind_dn=LDAP_BIND_DN,
        bind_password=LDAP_BIND_PASSWORD,
        base_dn=LDAP_BASE_DN,
        user_filter=OPENLDAP_USER_FILTER,
        group_filter=OPENLDAP_GROUP_FILTER,
    )
    session.add(directory)
    session.commit()
    session.refresh(directory)
    return directory


@pytest.fixture()
def test_directory_ad(session: Session):
    """Create a Directory record pointing at the local Samba AD container."""
    from app.models.directory import Directory

    directory = Directory(
        name="Test Samba AD",
        host=SAMBA_AD_HOST,
        port=SAMBA_AD_PORT,
        use_ssl=False,
        bind_dn=SAMBA_AD_BIND_DN,
        bind_password=SAMBA_AD_BIND_PASSWORD,
        base_dn=SAMBA_AD_BASE_DN,
        user_filter=SAMBA_AD_USER_FILTER,
        group_filter=SAMBA_AD_GROUP_FILTER,
    )
    session.add(directory)
    session.commit()
    session.refresh(directory)
    return directory


@pytest.fixture()
def api_client(test_engine):
    """Return a FastAPI TestClient wired to the test database."""
    os.environ["SECRET_KEY"] = "test-secret"
    os.environ["DATABASE_URL"] = TEST_DB_URL

    from app.db import get_session
    from app.main import app

    def _override_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = _override_session

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    app.dependency_overrides.clear()
