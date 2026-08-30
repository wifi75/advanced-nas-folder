"""Indirizzi corti: `/nome` porta alla cartella pubblicata con quel nome.

Perche esistono: il pannello vive sotto `/pannello/`, e l'indirizzo completo
di una cartella pubblicata e quindi
`https://sito/pannello/archivio/documenti`. E corretto ma non e un indirizzo
che si detta al telefono, ne che si scrive a mano senza sbagliare.

Come funzionano: il web server riceve una regola **per ogni pubblicazione**,
mai una regola che cattura tutto. Su un sito che ospita anche altro — ed e il
caso normale, non l'eccezione — una regola generica oscurerebbe i contenuti
degli altri, e lo farebbe in silenzio.

Il file viene riscritto per intero a ogni cambiamento, a partire dall'elenco
delle pubblicazioni attive: cosi non esistono aggiunte e rimozioni da tenere
in pari, e una scorciatoia non puo sopravvivere alla pubblicazione che l'aveva
creata.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Share
from app.services import agent_client

logger = logging.getLogger("anf.scorciatoie")


def webserver_in_uso() -> str | None:
    """Quale web server consegna i file, dedotto da come li consegna.

    Non c'e una impostazione separata di proposito: sarebbe una seconda fonte
    di verita che puo divergere da quella vera.
    """
    match get_settings().download_backend:
        case "xsendfile":
            return "apache"
        case "xaccel":
            return "nginx"
        case _:
            return None


async def riallinea(sessione: AsyncSession) -> dict[str, Any]:
    """Riscrive le scorciatoie a partire dalle pubblicazioni attive.

    Non solleva: un problema del web server non deve impedire di creare o
    togliere una pubblicazione, che e una operazione sul database. L'esito
    viene restituito perche il pannello possa mostrarlo.
    """
    ws = webserver_in_uso()
    if ws is None:
        return {"applicate": False, "motivo": "In sviluppo i file non passano dal web server."}

    righe = await sessione.execute(select(Share.slug).where(Share.is_enabled.is_(True)))
    slug = sorted(righe.scalars().all())

    try:
        esito = await agent_client.chiedi(
            "scorciatoie.write", {"webserver": ws, "slug": slug}, timeout=60
        )
    except Exception as errore:  # noqa: BLE001 - l'esito va riportato, non propagato
        logger.warning("scorciatoie non applicate: %s", errore)
        return {"applicate": False, "motivo": str(errore), "slug": slug}

    return {"applicate": True, "slug": slug, **esito}
