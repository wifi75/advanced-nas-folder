"""Consultazione e download delle cartelle pubblicate.

E' l'unica parte dell'API che risponde anche a chi non ha effettuato
l'accesso: una cartella pubblicata come pubblica dev'essere raggiungibile da
chiunque, altrimenti quella visibilita' non significherebbe nulla.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path, PurePosixPath

import anyio
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse

from app.api.deps import Sessione, UtenteFacoltativo
from app.core.security import (
    crea_gettone_percorso,
    verifica_gettone_percorso,
    verifica_password,
)
from app.models import Share, User
from app.models.enums import Visibilita
from app.schemas.archivio import (
    CompletaCaricamento,
    ContenutoOut,
    CreaCartella,
    Elimina,
    GettoneOut,
    RichiestaGettone,
    Rinomina,
    StatoCaricamento,
    Trasferisci,
    VoceOut,
)
from app.services import acl, archivio, caricamento, consegna, operazioni
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


# --- modifiche --------------------------------------------------------------


async def _con_scrittura(
    sessione: Sessione, share: Share, percorso: str, utente: User | None
) -> Path:
    """Autorizza in scrittura un percorso e restituisce il percorso reale.

    La scrittura non e' solo «accesso consentito»: serve un permesso di
    livello scrittura, oppure essere amministratori. Chi puo' leggere una
    cartella non deve poterne cambiare il contenuto.
    """
    decisione = await _autorizza(sessione, share, percorso, utente)
    if not decisione.scrittura:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Non hai il permesso di modificare questa cartella."
        )
    return await _reale(sessione, share, percorso)


async def _prepara(
    sessione: Sessione, slug: str, percorso: str, utente: User | None
) -> tuple[Share, str, Path]:
    share = await _pubblicazione(sessione, slug)
    normalizzato = _normalizza(percorso)
    return share, normalizzato, await _con_scrittura(sessione, share, normalizzato, utente)


def _rifiuto(exc: operazioni.OperazioneRifiutata) -> HTTPException:
    # 409 e non 400: la richiesta e' ben formata, e' lo stato della cartella
    # che non permette l'operazione — un nome gia' occupato, una cartella non
    # vuota. All'utente serve sapere questo, non «richiesta non valida».
    return HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.post("/{slug}/cartella", status_code=status.HTTP_201_CREATED)
async def crea_cartella(
    slug: str, dati: CreaCartella, sessione: Sessione, utente: UtenteFacoltativo
) -> dict[str, str]:
    _, percorso, reale = await _prepara(sessione, slug, dati.percorso, utente)
    try:
        await operazioni.crea_cartella(reale, dati.nome)
    except operazioni.OperazioneRifiutata as exc:
        raise _rifiuto(exc) from exc
    return {"percorso": str(PurePosixPath(percorso) / dati.nome.strip())}


@router.post("/{slug}/rinomina")
async def rinomina(
    slug: str, dati: Rinomina, sessione: Sessione, utente: UtenteFacoltativo
) -> dict[str, str]:
    _, percorso, reale = await _prepara(sessione, slug, dati.percorso, utente)
    try:
        await operazioni.rinomina(reale, dati.nome)
    except operazioni.OperazioneRifiutata as exc:
        raise _rifiuto(exc) from exc
    return {"percorso": str(PurePosixPath(percorso).parent / dati.nome.strip())}


@router.post("/{slug}/sposta")
async def sposta(
    slug: str, dati: Trasferisci, sessione: Sessione, utente: UtenteFacoltativo
) -> dict[str, str]:
    """Sposta un elemento in un'altra cartella.

    Servono i permessi di scrittura su **entrambe**: spostare significa
    togliere di la' e mettere di qua, e chiederli solo sulla destinazione
    permetterebbe di svuotare una cartella su cui non si ha alcun diritto.
    """
    share, origine, reale_origine = await _prepara(sessione, slug, dati.percorso, utente)
    destinazione = _normalizza(dati.destinazione)
    reale_destinazione = await _con_scrittura(sessione, share, destinazione, utente)

    try:
        await operazioni.sposta(reale_origine, reale_destinazione)
    except operazioni.OperazioneRifiutata as exc:
        raise _rifiuto(exc) from exc
    return {"percorso": str(PurePosixPath(destinazione) / PurePosixPath(origine).name)}


@router.post("/{slug}/copia")
async def copia(
    slug: str, dati: Trasferisci, sessione: Sessione, utente: UtenteFacoltativo
) -> dict[str, str]:
    """Copia un elemento in un'altra cartella.

    Qui basta poter leggere l'origine — copiarla non la cambia — ma serve
    scrivere nella destinazione.
    """
    share = await _pubblicazione(sessione, slug)
    origine = _normalizza(dati.percorso)
    await _autorizza(sessione, share, origine, utente)
    reale_origine = await _reale(sessione, share, origine)

    destinazione = _normalizza(dati.destinazione)
    reale_destinazione = await _con_scrittura(sessione, share, destinazione, utente)

    try:
        await operazioni.copia(reale_origine, reale_destinazione, dati.nome)
    except operazioni.OperazioneRifiutata as exc:
        raise _rifiuto(exc) from exc
    nome = dati.nome.strip() if dati.nome else PurePosixPath(origine).name
    return {"percorso": str(PurePosixPath(destinazione) / nome)}


@router.post("/{slug}/elimina", status_code=status.HTTP_204_NO_CONTENT)
async def elimina(slug: str, dati: Elimina, sessione: Sessione, utente: UtenteFacoltativo) -> None:
    """Elimina un file o una cartella.

    E' una POST e non una DELETE perche' serve un corpo: la conferma per una
    cartella non vuota non puo' viaggiare come parametro, dove finirebbe nei
    log del web server accanto al percorso di cio' che si sta cancellando.
    """
    _, percorso, reale = await _prepara(sessione, slug, dati.percorso, utente)
    if not percorso:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Non si può eliminare la radice della pubblicazione."
        )
    try:
        await operazioni.elimina(reale, ricorsivo=dati.ricorsivo)
    except operazioni.OperazioneRifiutata as exc:
        raise _rifiuto(exc) from exc


# --- caricamento ------------------------------------------------------------


@router.get("/{slug}/carica/stato", response_model=StatoCaricamento)
async def stato_caricamento(
    slug: str,
    sessione: Sessione,
    utente: UtenteFacoltativo,
    nome: str = Query(min_length=1, max_length=255),
    percorso: str = Query(default="", max_length=1024),
) -> StatoCaricamento:
    """Dice da dove riprendere un caricamento interrotto.

    Lo stato non vive in un database ma nel file parziale stesso: quanti byte
    sono arrivati lo dice la sua dimensione. Un caricamento interrotto ieri
    riprende oggi senza che nessuno se ne sia dovuto ricordare.
    """
    _, _, reale = await _prepara(sessione, slug, percorso, utente)
    try:
        stato = await caricamento.stato(reale, nome)
    except operazioni.OperazioneRifiutata as exc:
        raise _rifiuto(exc) from exc
    return StatoCaricamento(
        nome=stato.nome, ricevuti=stato.ricevuti, gia_presente=stato.gia_presente
    )


@router.put("/{slug}/carica")
async def carica_blocco(
    slug: str,
    richiesta: Request,
    sessione: Sessione,
    utente: UtenteFacoltativo,
    nome: str = Query(min_length=1, max_length=255),
    offset: int = Query(ge=0),
    percorso: str = Query(default="", max_length=1024),
) -> dict[str, int]:
    """Riceve un blocco e lo aggiunge in coda al file parziale.

    Il corpo e' il blocco grezzo, non un modulo multipart: incapsularlo
    costringerebbe a rileggere e ricopiare gli stessi byte due volte per
    nulla.
    """
    _, _, reale = await _prepara(sessione, slug, percorso, utente)

    blocco = await richiesta.body()
    if not blocco:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Il blocco inviato è vuoto.")

    try:
        ricevuti = await caricamento.aggiungi(reale, nome, blocco, offset)
    except operazioni.OperazioneRifiutata as exc:
        raise _rifiuto(exc) from exc
    return {"ricevuti": ricevuti}


@router.post("/{slug}/carica/completa", status_code=status.HTTP_201_CREATED)
async def completa_caricamento(
    slug: str, dati: CompletaCaricamento, sessione: Sessione, utente: UtenteFacoltativo
) -> dict[str, str]:
    """Trasforma il file parziale nel file definitivo.

    La rinomina finale e' atomica: non esiste un istante in cui il file esiste
    ma e' incompleto, e chi lo scarica non puo' trovarne meta'.
    """
    _, percorso, reale = await _prepara(sessione, slug, dati.percorso, utente)
    try:
        definitivo = await caricamento.completa(reale, dati.nome, dati.dimensione)
    except operazioni.OperazioneRifiutata as exc:
        raise _rifiuto(exc) from exc
    return {"percorso": str(PurePosixPath(percorso) / definitivo.name)}


@router.post("/{slug}/carica/annulla", status_code=status.HTTP_204_NO_CONTENT)
async def annulla_caricamento(
    slug: str, dati: CompletaCaricamento, sessione: Sessione, utente: UtenteFacoltativo
) -> None:
    """Butta via un caricamento a metà.

    Senza, un file parziale abbandonato resterebbe a occupare spazio sul NAS
    senza che nessuno sappia più cosa fosse.
    """
    _, _, reale = await _prepara(sessione, slug, dati.percorso, utente)
    try:
        await caricamento.annulla(reale, dati.nome)
    except operazioni.OperazioneRifiutata as exc:
        raise _rifiuto(exc) from exc
