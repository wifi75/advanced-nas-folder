"""Punto di ingresso dell'API di Advanced NAS Folder."""

from fastapi import FastAPI

from app.core.version import (
    APP_AUTHOR,
    APP_DESCRIPTION,
    APP_FOOTER,
    APP_NAME,
    APP_VERSION,
)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=f"{APP_DESCRIPTION}\n\n{APP_FOOTER}",
)


@app.get("/api/v1/health", tags=["stato"])
async def health() -> dict[str, str]:
    """Stato del servizio, versione e attribuzione.

    Il frontend legge questo endpoint all'avvio per comporre la riga a pie di
    pagina, cosi la versione non e scritta a mano in piu punti.
    """
    return {
        "status": "ok",
        "name": APP_NAME,
        "version": APP_VERSION,
        "author": APP_AUTHOR,
    }
