"""Monitoraggio dei trasferimenti.

Il flusso dal vivo usa **SSE** e non WebSocket. Il motivo è pratico: qui i dati
vanno in una sola direzione, e un WebSocket dietro Apache richiede
`mod_proxy_wstunnel` e una configurazione in più che qualcuno dimenticherà.
Una risposta che non finisce mai passa da qualunque proxy senza chiedere nulla
a nessuno, e il browser la riconnette da solo se cade.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import Amministratore, Sessione
from app.models import Transfer
from app.schemas.archivio import TrasferimentoOut
from app.services import trasferimenti

router = APIRouter(prefix="/trasferimenti", tags=["monitoraggio"])

#: Ogni tanto si manda un commento per tenere viva la connessione: senza, un
#: proxy che chiude le connessioni inattive taglierebbe il flusso proprio
#: quando non succede nulla, cioè quando sembra tutto a posto.
_BATTITO = 25.0


@router.get("", response_model=list[TrasferimentoOut])
async def elenca(sessione: Sessione, _: Amministratore, limite: int = 100) -> list[Transfer]:
    return await trasferimenti.recenti(sessione, min(limite, 500))


@router.get("/flusso")
async def flusso(_: Amministratore) -> StreamingResponse:
    """Gli eventi man mano che succedono, come flusso SSE."""

    async def eventi() -> AsyncIterator[str]:
        sorgente: AsyncGenerator[dict[str, Any]] = trasferimenti.flusso()
        try:
            while True:
                try:
                    evento = await asyncio.wait_for(anext(sorgente), timeout=_BATTITO)
                except TimeoutError:
                    yield ": battito\n\n"
                    continue
                yield f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"
        finally:
            with contextlib.suppress(Exception):
                await sorgente.aclose()

    return StreamingResponse(
        eventi(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            # Dice a Nginx di non accumulare la risposta: senza, il flusso
            # arriverebbe a blocchi e in ritardo, cioè non sarebbe dal vivo.
            "X-Accel-Buffering": "no",
        },
    )
