"""Punto di ingresso dell'API di Advanced NAS Folder."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import (
    archivio,
    auth,
    health,
    impostazioni,
    link,
    mounts,
    shares,
    trasferimenti,
    utenti,
    vhosts,
)
from app.core.config import get_settings
from app.core.database import engine
from app.core.version import (
    APP_AUTHOR,
    APP_DESCRIPTION,
    APP_FOOTER,
    APP_NAME,
    APP_VERSION,
)
from app.models import Base
from app.services import accesslog
from app.services.bootstrap import crea_amministratore_iniziale

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

    if settings.is_dev:
        # In sviluppo le tabelle si creano da sole, per non dover lanciare le
        # migrazioni a ogni riavvio. In produzione le applica l'installer.
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    await crea_amministratore_iniziale()

    # I byte davvero trasferiti li conosce solo il web server: se e' stato
    # indicato il suo access log, lo si segue in sottofondo per aggiornarli.
    sorveglianza: asyncio.Task[None] | None = None
    if settings.access_log is not None:
        sorveglianza = asyncio.create_task(accesslog.sorveglia(settings.access_log))

    yield

    if sorveglianza is not None:
        sorveglianza.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sorveglianza
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
app.include_router(auth.router, prefix="/api/v1")
app.include_router(mounts.router, prefix="/api/v1")
app.include_router(shares.router, prefix="/api/v1")
app.include_router(archivio.router, prefix="/api/v1")
app.include_router(link.router, prefix="/api/v1")
app.include_router(vhosts.router, prefix="/api/v1")
app.include_router(utenti.router, prefix="/api/v1")
app.include_router(trasferimenti.router, prefix="/api/v1")
app.include_router(impostazioni.router, prefix="/api/v1")
