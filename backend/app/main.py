"""Punto di ingresso dell'API di Advanced NAS Folder."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import health
from app.core.config import get_settings
from app.core.database import engine
from app.core.version import (
    APP_AUTHOR,
    APP_DESCRIPTION,
    APP_FOOTER,
    APP_NAME,
    APP_VERSION,
)

logger = logging.getLogger("anf")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    )
    logger.info("%s v%s in avvio (%s)", APP_NAME, APP_VERSION, settings.env)
    logger.info("Database: %s", settings.db_path)
    yield
    await engine.dispose()
    logger.info("%s arrestato", APP_NAME)


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=f"{APP_DESCRIPTION}\n\n{APP_FOOTER}",
    contact={"name": APP_AUTHOR},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    lifespan=lifespan,
)

app.include_router(health.router, prefix="/api/v1")
