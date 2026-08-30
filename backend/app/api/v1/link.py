"""Accesso pubblico tramite link di condivisione.

Chi arriva da un link non ha un account e non lo avrà: il token è
l'autorizzazione. Vale solo per il ramo, la scadenza e il numero di
scaricamenti decisi da chi l'ha creato — vedere `services/link.py`.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import anyio
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import Sessione
from app.core.security import verifica_password
from app.models import Share, ShareLink
from app.schemas.archivio import ContenutoOut, VoceOut
from app.services import archivio, consegna, trasferimenti
from app.services import link as servizio_link
from app.services.percorsi import PercorsoNonValido, normalizza_relativo, risolvi

router = APIRouter(prefix="/link", tags=["link di condivisione"])

#: Stessa risposta per token inesistente, scaduto, revocato o esaurito: dire
#: quale dei quattro permetterebbe di sondare quali token esistono.
_NON_VALIDO = HTTPException(
    status.HTTP_404_NOT_FOUND, "Questo collegamento non è valido o non è più disponibile."
)


async def _apri(
    sessione: Sessione, token: str, percorso: str, password: str | None
) -> tuple[ShareLink, Share, str]:
    """Trova il link, ne verifica la validità e restituisce il percorso normalizzato."""
    risultato = await sessione.execute(
        select(ShareLink).where(ShareLink.token_hash == servizio_link.impronta(token))
    )
    collegamento = risultato.scalar_one_or_none()
    if collegamento is None:
        raise _NON_VALIDO

    share = await sessione.get(Share, collegamento.share_id)
    if share is None:
        raise _NON_VALIDO

    # Le regole servono a `verifica`, che deve poter vedere un divieto
    # esplicito sul percorso: un link non lo supera.
    await sessione.refresh(share, ["rules"])

    try:
        richiesto = str(normalizza_relativo(percorso)) if percorso.strip() not in ("", "/") else ""
    except PercorsoNonValido as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    # Senza percorso si atterra sul ramo del link, non sulla radice della
    # pubblicazione: il collegamento *e'* quella cartella, e chi lo apre si
    # aspetta di vedersela davanti, non un errore.
    if not richiesto:
        richiesto = collegamento.path

    # Fuori dal ramo del link il percorso non esiste, per chi ha quel token.
    if not servizio_link.dentro_ramo(collegamento, richiesto):
        raise _NON_VALIDO

    esito = servizio_link.verifica(collegamento, share, richiesto)
    if not esito.valido:
        raise HTTPException(status.HTTP_403_FORBIDDEN, esito.motivo)

    if collegamento.password_hash is not None and not (
        password is not None and verifica_password(password, collegamento.password_hash)
    ):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Questo collegamento è protetto da una password."
        )

    return collegamento, share, richiesto


async def _reale(sessione: Sessione, share: Share, percorso: str) -> Path:
    try:
        return risolvi(await archivio.radice(sessione, share), percorso)
    except PercorsoNonValido as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except archivio.ArchivioNonDisponibile as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc


@router.get("/{token}", response_model=ContenutoOut)
async def contenuto(
    token: str,
    sessione: Sessione,
    percorso: str = Query(default="", max_length=1024),
    password: str | None = None,
) -> ContenutoOut:
    """Elenco della cartella raggiunta dal link."""
    collegamento, share, richiesto = await _apri(sessione, token, percorso, password)
    reale = await _reale(sessione, share, richiesto)

    def consentito(p: str) -> bool:
        return servizio_link.verifica(collegamento, share, p).valido

    try:
        # Gli stessi nomi nascosti valgono anche qui: chi riceve un link non
        # deve vedere il cestino del NAS piu' di chi entra dal pannello.
        voci = await archivio.elenca(
            reale, richiesto, consentito, schemi=archivio.schemi_da(share.hidden_patterns)
        )
    except archivio.ArchivioNonDisponibile as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return ContenutoOut(
        slug=share.slug,
        label=collegamento.label or share.label,
        descrizione=share.description,
        percorso=richiesto,
        # Le briciole partono dal ramo del link: mostrare le cartelle sopra
        # inviterebbe a risalire dove il collegamento non porta.
        briciole=archivio.briciole(richiesto)[len(archivio.briciole(collegamento.path)) :],
        voci=[VoceOut(**asdict(v)) for v in voci],
        scrittura=False,
        visibilita=share.default_visibility,
    )


@router.get("/{token}/file")
async def scarica(
    token: str,
    richiesta: Request,
    sessione: Sessione,
    percorso: str = Query(max_length=1024),
    password: str | None = None,
) -> Response:
    """Consegna un file attraverso il link, contando lo scaricamento."""
    collegamento, share, richiesto = await _apri(sessione, token, percorso, password)
    if not richiesto:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Indicare il file da scaricare.")

    reale = await _reale(sessione, share, richiesto)
    if not await anyio.to_thread.run_sync(reale.is_file):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File non trovato.")

    # Il conteggio si aggiorna prima di consegnare: il file lo invia il web
    # server, e a quel punto l'applicazione non sa più se e quando è finito.
    # Contare in anticipo può togliere uno scaricamento a un trasferimento
    # fallito; contare dopo non conterebbe affatto.
    collegamento.download_count += 1
    await sessione.commit()

    await trasferimenti.registra_download(
        sessione,
        richiesta=richiesta,
        share_id=share.id,
        percorso=richiesto,
        link_id=collegamento.id,
        dimensione=reale.stat().st_size,
    )

    preparata = consegna.prepara(reale, reale.name)
    if preparata.invia_direttamente is not None:
        return FileResponse(
            preparata.invia_direttamente,
            media_type=preparata.tipo,
            headers=preparata.intestazioni,
        )
    return Response(status_code=status.HTTP_200_OK, headers=preparata.intestazioni)
