"""Materialize effective (transitive) group memberships.

Uses a recursive CTE to walk the group hierarchy from every direct
user→group edge outward, storing one row per distinct path (Variante B).
This preserves the full audit trail for permissions analysis.
"""

from __future__ import annotations

import logging
import time
import uuid

from sqlalchemy import text
from sqlmodel import Session

logger = logging.getLogger(__name__)

_MATERIALIZE_SQL = text("""
WITH RECURSIVE membership_graph AS (
    -- Base case: direct user→group edges (depth 0)
    SELECT
        dm.directory_id,
        dm.child_dn   AS user_dn,
        dm.parent_dn  AS group_dn,
        0              AS depth,
        jsonb_build_array(dm.parent_dn) AS path
    FROM direct_memberships dm
    WHERE dm.directory_id = :directory_id
      AND dm.child_type = 'USER'

    UNION ALL

    -- Recursive case: follow group→group edges upward
    SELECT
        mg.directory_id,
        mg.user_dn,
        dm.parent_dn   AS group_dn,
        mg.depth + 1    AS depth,
        mg.path || jsonb_build_array(dm.parent_dn) AS path
    FROM membership_graph mg
    JOIN direct_memberships dm
      ON dm.directory_id = mg.directory_id
     AND dm.child_dn = mg.group_dn
     AND dm.child_type = 'GROUP'
    WHERE mg.depth < 20
)
INSERT INTO effective_memberships (id, directory_id, user_dn, group_dn, depth, path, created_at)
SELECT
    gen_random_uuid(),
    directory_id,
    user_dn,
    group_dn,
    depth,
    path,
    now()
FROM membership_graph
""")


def materialize_effective_memberships(
    directory_id: uuid.UUID,
    session: Session,
) -> int:
    """Rebuild the effective_memberships table for a directory.

    Returns the number of rows inserted.
    """
    t0 = time.monotonic()

    session.execute(
        text("DELETE FROM effective_memberships WHERE directory_id = :directory_id"),
        {"directory_id": directory_id},
    )

    result = session.execute(_MATERIALIZE_SQL, {"directory_id": directory_id})
    row_count = result.rowcount

    elapsed = time.monotonic() - t0
    logger.info(
        "Materialized %d effective memberships for directory %s in %.2fs",
        row_count,
        directory_id,
        elapsed,
    )
    return row_count
