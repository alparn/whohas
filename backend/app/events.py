from __future__ import annotations

import json
import logging
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.config import settings

logger = logging.getLogger(__name__)


def notify(channel: str, payload: dict[str, Any] | None = None) -> None:
    """Send a NOTIFY on *channel* with an optional JSON payload (sync/blocking)."""
    raw_url = settings.async_database_url
    with psycopg.connect(raw_url) as conn:
        msg = json.dumps(payload) if payload else ""
        conn.execute("SELECT pg_notify(%s, %s)", [channel, msg])
        logger.debug("NOTIFY %s → %s", channel, msg)


async def listen(channel: str) -> psycopg.AsyncConnection[dict_row]:  # type: ignore[type-arg]
    """Return an async connection that is already LISTENing on *channel*.

    Usage::

        aconn = await listen("sync_completed")
        async for notify in aconn.notifies():
            handle(notify)
    """
    raw_url = settings.async_database_url
    aconn = await psycopg.AsyncConnection.connect(raw_url, autocommit=True)
    await aconn.execute(f"LISTEN {channel}")
    logger.info("Listening on Postgres channel %s", channel)
    return aconn
