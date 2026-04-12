from __future__ import annotations

import logging
from typing import Any

from ldap3 import (
    ALL_ATTRIBUTES,
    AUTO_BIND_NO_TLS,
    AUTO_BIND_TLS_BEFORE_BIND,
    SUBTREE,
    Connection,
    Server,
)
from ldap3.core.exceptions import LDAPException

from app.models.directory import Directory

logger = logging.getLogger(__name__)

USER_OBJECT_FILTER = "(objectClass=user)"
GROUP_OBJECT_FILTER = "(objectClass=group)"

USER_ATTRS = [
    "distinguishedName",
    "sAMAccountName",
    "displayName",
    "mail",
    "lastLogon",
    "userAccountControl",
]

GROUP_ATTRS = [
    "distinguishedName",
    "cn",
    "description",
    "groupType",
]


class LDAPClient:
    """Synchronous LDAP client wrapping ldap3. Call from async context via run_in_threadpool."""

    def __init__(
        self,
        directory: Directory,
        user_filter: str = USER_OBJECT_FILTER,
        group_filter: str = GROUP_OBJECT_FILTER,
    ) -> None:
        self._directory = directory
        self._user_filter = user_filter
        self._group_filter = group_filter
        self._conn: Connection | None = None

    def connect(self) -> None:
        """Establish an authenticated connection to the LDAP server."""
        server = Server(
            self._directory.host,
            port=self._directory.port,
            use_ssl=self._directory.use_ssl,
            get_info="ALL",
        )
        auto_bind = AUTO_BIND_TLS_BEFORE_BIND if self._directory.use_ssl else AUTO_BIND_NO_TLS
        self._conn = Connection(
            server,
            user=self._directory.bind_dn,
            password=self._directory.bind_password,
            auto_bind=auto_bind,
            read_only=True,
        )
        logger.info("Connected to LDAP %s:%d", self._directory.host, self._directory.port)

    def disconnect(self) -> None:
        """Close the LDAP connection."""
        if self._conn:
            self._conn.unbind()
            self._conn = None
            logger.info("Disconnected from LDAP %s", self._directory.host)

    def _ensure_connected(self) -> Connection:
        if self._conn is None:
            raise LDAPException("Not connected — call connect() first")
        return self._conn

    def search_users(self, base_dn: str | None = None, page_size: int = 1000) -> list[dict[str, Any]]:
        """Paged search for all user objects under *base_dn*."""
        conn = self._ensure_connected()
        search_base = base_dn or self._directory.base_dn
        entries: list[dict[str, Any]] = []

        conn.search(
            search_base=search_base,
            search_filter=self._user_filter,
            search_scope=SUBTREE,
            attributes=ALL_ATTRIBUTES,
            paged_size=page_size,
        )
        entries.extend(_extract_entries(conn))

        while conn.result.get("controls", {}).get("1.2.840.113556.1.4.319", {}).get("value", {}).get("cookie"):
            cookie = conn.result["controls"]["1.2.840.113556.1.4.319"]["value"]["cookie"]
            conn.search(
                search_base=search_base,
                search_filter=self._user_filter,
                search_scope=SUBTREE,
                attributes=ALL_ATTRIBUTES,
                paged_size=page_size,
                paged_cookie=cookie,
            )
            entries.extend(_extract_entries(conn))

        logger.info("Fetched %d user entries from %s", len(entries), search_base)
        return entries

    def search_groups(self, base_dn: str | None = None, page_size: int = 1000) -> list[dict[str, Any]]:
        """Paged search for all group objects under *base_dn*."""
        conn = self._ensure_connected()
        search_base = base_dn or self._directory.base_dn
        entries: list[dict[str, Any]] = []

        conn.search(
            search_base=search_base,
            search_filter=self._group_filter,
            search_scope=SUBTREE,
            attributes=ALL_ATTRIBUTES,
            paged_size=page_size,
        )
        entries.extend(_extract_entries(conn))

        while conn.result.get("controls", {}).get("1.2.840.113556.1.4.319", {}).get("value", {}).get("cookie"):
            cookie = conn.result["controls"]["1.2.840.113556.1.4.319"]["value"]["cookie"]
            conn.search(
                search_base=search_base,
                search_filter=self._group_filter,
                search_scope=SUBTREE,
                attributes=ALL_ATTRIBUTES,
                paged_size=page_size,
                paged_cookie=cookie,
            )
            entries.extend(_extract_entries(conn))

        logger.info("Fetched %d group entries from %s", len(entries), search_base)
        return entries


def _extract_entries(conn: Connection) -> list[dict[str, Any]]:
    """Convert ldap3 response entries to plain dicts safe for JSON serialization."""
    results: list[dict[str, Any]] = []
    for entry in conn.entries:
        attrs = entry.entry_attributes_as_dict
        flat: dict[str, Any] = {}
        for key, value in attrs.items():
            cleaned = _make_json_safe(value)
            flat[key] = cleaned[0] if isinstance(cleaned, list) and len(cleaned) == 1 else cleaned
        flat["dn"] = entry.entry_dn
        results.append(flat)
    return results


def _make_json_safe(value: Any) -> Any:
    """Recursively convert bytes, datetimes, and other non-JSON-serializable types."""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.hex()
    if isinstance(value, list):
        return [_make_json_safe(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
