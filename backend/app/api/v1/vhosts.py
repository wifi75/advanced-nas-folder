"""Pubblicazione del pannello sul web server.

È il passaggio che finora si faceva a mano, ed è quello in cui si sbaglia di
più: la configurazione che fa funzionare i download (`XSendFilePath` in
Apache, una `location internal` in Nginx) è facile da dimenticare e pericolosa
da scrivere male. Qui la genera l'agent, che la prova prima di applicarla e
**rimette la precedente se il test fallisce**.

Quello che il pannello non fa, e non deve far credere di fare: DNS,
certificati e ascolto in HTTPS. Vivono a monte, tipicamente su un reverse
proxy, e fingere di gestirli produrrebbe configurazioni che non corrispondono
alla realtà dell'impianto.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import Amministratore, Sessione
from app.api.errori import errore_agent
from app.core.config import get_settings
from app.models import Share, VHost
from app.models.enums import WebServer
from app.schemas.archivio import (
    VHostAnteprima,
    VHostCreate,
    VHostOut,
    WebServerDisponibili,
)
from app.services import agent_client

router = APIRouter(prefix="/vhosts", tags=["web server"])


def _dati(dati: VHostCreate) -> dict[str, Any]:
    """Argomenti per l'agent.

    La radice dei mount non compare qui: la conosce l'agent, che è stato
    avviato con quella. Mandargliela dall'API significherebbe poter far servire
    al web server una cartella qualunque del disco.
    """
    settings = get_settings()
    return {
        "webserver": dati.webserver.value,
        "hostname": dati.hostname,
        "prefisso": dati.prefisso,
        "porta": settings.port,
        "cartella_pannello": str(settings.panel_dir).replace("\\", "/"),
        "prefisso_interno": settings.xaccel_prefix,
    }


async def _chiedi(verbo: str, dati: dict[str, Any]) -> dict[str, Any]:
    try:
        return await agent_client.chiedi(verbo, dati, timeout=60)
    except (agent_client.AgentNonDisponibile, agent_client.AgentRifiuta) as exc:
        raise errore_agent(exc) from exc


@router.get("/disponibili", response_model=WebServerDisponibili)
async def disponibili(_: Amministratore) -> WebServerDisponibili:
    """Quali web server risultano installati sulla macchina."""
    risposta = await _chiedi("webserver.detect", {})
    trovati = risposta.get("installati") or []
    ammessi = {w.value for w in WebServer}
    # Si filtra invece di fidarsi: l'agent e l'API possono trovarsi a versioni
    # diverse dopo un aggiornamento a meta, e un nome sconosciuto qui
    # diventerebbe un errore di validazione incomprensibile.
    return WebServerDisponibili(
        installati=[WebServer(n) for n in trovati if isinstance(n, str) and n in ammessi]
    )


@router.get("", response_model=list[VHostOut])
async def elenca(sessione: Sessione, _: Amministratore) -> list[VHost]:
    risultato = await sessione.execute(select(VHost).order_by(VHost.hostname))
    return list(risultato.scalars().all())


@router.post("/anteprima", response_model=VHostAnteprima)
async def anteprima(dati: VHostCreate, _: Amministratore) -> VHostAnteprima:
    """Mostra la configurazione **prima** di scriverla.

    Chi amministra un server vuole vedere cosa sta per finire in
    `sites-available` prima che ci finisca, e non c'è ragione di negarglielo.
    """
    risposta = await _chiedi("vhost.preview", _dati(dati))
    return VHostAnteprima(configurazione=str(risposta.get("configurazione", "")))


@router.post("", response_model=VHostOut, status_code=status.HTTP_201_CREATED)
async def crea(dati: VHostCreate, sessione: Sessione, _: Amministratore) -> VHost:
    """Scrive il vhost, lo prova e lo attiva."""
    if dati.share_id is not None and await sessione.get(Share, dati.share_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La pubblicazione indicata non esiste.")

    esistente = await sessione.execute(
        select(VHost).where(VHost.hostname == dati.hostname, VHost.webserver == dati.webserver)
    )
    if esistente.scalar_one_or_none() is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"{dati.hostname} è già configurato su questo web server."
        )

    risposta = await _chiedi("vhost.write", _dati(dati))

    vhost = VHost(
        hostname=dati.hostname,
        path_prefix=dati.prefisso,
        share_id=dati.share_id,
        webserver=dati.webserver,
        is_enabled=True,
        # Si conserva ciò che è stato scritto davvero, non ciò che si voleva
        # scrivere: è l'unico modo di sapere poi cosa c'è sul disco.
        rendered_config=str(risposta.get("configurazione", "")),
    )
    sessione.add(vhost)
    await sessione.commit()
    await sessione.refresh(vhost)
    return vhost


@router.get("/{vhost_id}/configurazione", response_model=VHostAnteprima)
async def configurazione(vhost_id: int, sessione: Sessione, _: Amministratore) -> VHostAnteprima:
    """La configurazione realmente scritta per questo vhost."""
    vhost = await sessione.get(VHost, vhost_id)
    if vhost is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vhost non trovato.")
    return VHostAnteprima(configurazione=vhost.rendered_config or "")


@router.delete("/{vhost_id}", status_code=status.HTTP_204_NO_CONTENT)
async def elimina(vhost_id: int, sessione: Sessione, _: Amministratore) -> None:
    """Toglie il vhost dal web server e dal pannello.

    Prima il file, poi la riga: se si cancellasse prima la riga e la rimozione
    fallisse, resterebbe sul server una configurazione che il pannello non sa
    più di avere scritto.
    """
    vhost = await sessione.get(VHost, vhost_id)
    if vhost is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vhost non trovato.")

    await _chiedi("vhost.remove", {"webserver": vhost.webserver.value, "hostname": vhost.hostname})
    await sessione.delete(vhost)
    await sessione.commit()
