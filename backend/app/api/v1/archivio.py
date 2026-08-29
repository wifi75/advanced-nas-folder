"""Consultazione e download delle cartelle pubblicate.

E' l'unica parte dell'API che risponde anche a chi non ha effettuato
l'accesso: una cartella pubblicata come pubblica dev'essere raggiungibile da
chiunque, altrimenti quella visibilita' non significherebbe nulla.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import anyio
from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import FileResponse

from app.api.deps import Sessione, UtenteFacoltativo
from app.core.security import (
    crea_gettone_percorso,
    verifica_gettone_percorso,
    verifica_password,
)
from app.models import Share, User
from app.models.enums import Visibilita
from app.schemas.archivio import ContenutoOut, GettoneOut, RichiestaGettone, VoceOut
from app.services import acl, archivio, consegna
from app.services.percorsi import PercorsoNonValido, normalizza_relativo, risolvi

router = APIRouter(prefix="/archivio", tags=["archivio"])

#: Durata del gettone di download. Abbastanza perche' l'utente faccia partire
#: il download, troppo poco perche' un collegamento copiato resti utile.
_MINUTI_GETTONE = 5

_NEGATO = HTTPException(status.HTTP_403_FORBIDDEN, "Accesso non consentito a questo percorso.")


async def _pubblicazione(sessione: Sessione, slug: str) -> Share:
    share = await archivio.carica_per_slug(sessione, slug)
    if share is None or not share.is_enabled:
        # Stessa risposta per "non esiste" e "disattivata": distinguerle
        # direbbe a chiunque quali pubblicazioni esistono.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pubblicazione non trovata.")
    return share


def _password_valida(share: Share, percorso: str, password: str | None) -> bool:
    """Vero se la password fornita apre il percorso richiesto."""
    if password is None:
        return False
    regola = acl.regola_applicabile(share, percorso)
    if regola is None or regola.visibility is not Visibilita.PASSWORD:
        return False
    return regola.password_hash is not None and verifica_password(password, regola.password_hash)


async def _autorizza(
    sessione: Sessione,
    share: Share,
    percorso: str,
    utente: User | None,
    password: str | None = None,
) -> acl.Decisione:
    permessi = await archivio.permessi_di(sessione, share.id, utente)
    decisione = acl.valuta(
        share,
        percorso,
        utente,
        permessi=permessi,
        password_fornita=_password_valida(share, percorso, password),
    )
    if not decisione.consentito or not acl.dentro_ambito(utente, percorso):
        raise _NEGATO
    return decisione


def _normalizza(percorso: str) -> str:
    try:
        return str(normalizza_relativo(percorso)) if percorso.strip() not in ("", "/") else ""
    except PercorsoNonValido as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


async def _reale(sessione: Sessione, share: Share, percorso: str) -> Path:
    try:
        radice = await archivio.radice(sessione, share)
        return risolvi(radice, percorso)
    except PercorsoNonValido as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except archivio.ArchivioNonDisponibile as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc


# --- consultazione ---------------------------------------------------------


@router.get("/{slug}", response_model=ContenutoOut)
async def contenuto(
    slug: str,
    sessione: Sessione,
    utente: UtenteFacoltativo,
    percorso: str = Query(default="", max_length=1024),
    password: str | None = None,
) -> ContenutoOut:
    """Elenco della cartella, limitato alle voci che chi guarda puo' vedere."""
    share = await _pubblicazione(sessione, slug)
    percorso = _normalizza(percorso)
    decisione = await _autorizza(sessione, share, percorso, utente, password)

    reale = await _reale(sessione, share, percorso)
    permessi = await archivio.permessi_di(sessione, share.id, utente)

    def consentito(p: str) -> bool:
        return acl.valuta(share, p, utente, permessi=permessi).consentito and acl.dentro_ambito(
            utente, p
        )

    try:
        voci = await archivio.elenca(reale, percorso, consentito)
    except archivio.ArchivioNonDisponibile as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return ContenutoOut(
        slug=share.slug,
        label=share.label,
        descrizione=share.description,
        percorso=percorso,
        briciole=archivio.briciole(percorso),
        voci=[VoceOut(**asdict(v)) for v in voci],
        scrittura=decisione.scrittura,
        visibilita=decisione.visibilita,
    )


@router.post("/{slug}/gettone", response_model=GettoneOut)
async def gettone(
    slug: str, dati: RichiestaGettone, sessione: Sessione, utente: UtenteFacoltativo
) -> GettoneOut:
    """Rilascia l'autorizzazione da mettere nel collegamento di download.

    Qui l'accesso viene verificato per intero — sessione, permessi, password —
    una volta sola; il collegamento che ne esce non deve piu' portare segreti.
    """
    share = await _pubblicazione(sessione, slug)
    percorso = _normalizza(dati.percorso)
    await _autorizza(sessione, share, percorso, utente, dati.password)

    return GettoneOut(
        gettone=crea_gettone_percorso(share.id, percorso, minuti=_MINUTI_GETTONE),
        valido_secondi=_MINUTI_GETTONE * 60,
    )


# --- download --------------------------------------------------------------


@router.get("/{slug}/file")
async def scarica(
    slug: str,
    sessione: Sessione,
    utente: UtenteFacoltativo,
    percorso: str = Query(max_length=1024),
    g: str | None = Query(default=None, description="Gettone rilasciato da /gettone"),
) -> Response:
    """Consegna un file.

    L'applicazione non invia i byte: autorizza e passa il file al web server,
    che sa gia' rispondere a `Range` e quindi riprendere un download
    interrotto. Vedere `services/consegna.py`.
    """
    share = await _pubblicazione(sessione, slug)
    percorso = _normalizza(percorso)
    if not percorso:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Indicare il file da scaricare.")

    # Il gettone vale solo per il percorso per cui e' stato emesso, e l'accesso
    # e' gia' stato verificato al momento del rilascio.
    if g is None or not verifica_gettone_percorso(g, share.id, percorso):
        await _autorizza(sessione, share, percorso, utente)

    reale = await _reale(sessione, share, percorso)
    if not await anyio.to_thread.run_sync(reale.is_file):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File non trovato.")

    preparata = consegna.prepara(reale, reale.name)
    if preparata.invia_direttamente is not None:
        return FileResponse(
            preparata.invia_direttamente,
            media_type=preparata.tipo,
            headers=preparata.intestazioni,
        )
    return Response(status_code=status.HTTP_200_OK, headers=preparata.intestazioni)
