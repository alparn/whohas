# whohas — Copyright (C) 2026 whohas contributors

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.directories import router as directories_router
from app.api.graph import router as graph_router
from app.api.groups import router as groups_router
from app.api.insights import router as insights_router
from app.api.memberships import router as memberships_router
from app.api.sync import router as sync_router
from app.api.users import router as users_router
from app.config import settings
from app.services.sync import sync_all_directories

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start the background sync scheduler on startup, shut it down on exit."""
    scheduler.add_job(
        sync_all_directories,
        "interval",
        minutes=settings.SYNC_INTERVAL_MINUTES,
        id="ldap_sync",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Sync scheduler started — running every %d minutes",
        settings.SYNC_INTERVAL_MINUTES,
    )
    yield
    scheduler.shutdown(wait=False)
    logger.info("Sync scheduler stopped")


app = FastAPI(
    title="whohas",
    description="Identity Intelligence Layer — AD/LDAP visualization, search, and analytics",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(directories_router)
app.include_router(graph_router)
app.include_router(groups_router)
app.include_router(insights_router)
app.include_router(memberships_router)
app.include_router(sync_router)
app.include_router(users_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
