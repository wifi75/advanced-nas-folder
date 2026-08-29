"""Endpoint di stato."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.version import APP_AUTHOR, APP_NAME, APP_VERSION

router = APIRouter(tags=["stato"])

#: Sessione del database iniettata da FastAPI. Dichiarata come alias di tipo e
#: non come valore predefinito dell'argomento: quest'ultima forma esegue la
#: chiamata a Depends() al momento della definizione della funzione.
Sessione = Annotated[AsyncSession, Depends(get_session)]


@router.get("/health")
async def health() -> dict[str, str]:
    """Stato, versione e attribuzione.

    Il frontend lo chiama all'avvio per comporre la riga a pie di pagina, cosi
    la versione non e scritta a mano in piu punti.
    """
    return {
        "status": "ok",
        "name": APP_NAME,
        "version": APP_VERSION,
        "author": APP_AUTHOR,
    }


@router.get("/health/ready")
async def ready(session: Sessione) -> dict[str, Any]:
    """Verifica che il database risponda davvero.

    Separato da /health di proposito: un servizio puo essere avviato e avere il
    database irraggiungibile, e i due casi vanno distinti.
    """
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - qualunque errore qui e "non pronto"
        return {"status": "degraded", "database": "irraggiungibile", "detail": str(exc)}
    return {"status": "ok", "database": "ok"}
