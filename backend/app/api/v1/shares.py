"""Cartelle pubblicate, regole di accesso e permessi degli utenti."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import Amministratore, Sessione
from app.core.security import hash_password
from app.models import AccessRule, Mount, PermessoUtente, Share, ShareLink, User
from app.models.enums import Visibilita
from app.schemas.archivio import LinkCreate, LinkCreato, LinkOut
from app.schemas.share import (
    EsitoAccesso,
    PermessoCreate,
    PermessoOut,
    ProvaAccesso,
    RegolaCreate,
    RegolaOut,
    ShareCreate,
    ShareDettaglio,
    ShareOut,
    ShareUpdate,
)
from app.services import acl, archivio, scorciatoie
from app.services import link as servizio_link
from app.services.percorsi import PercorsoNonValido, normalizza_relativo

router = APIRouter(prefix="/shares", tags=["pubblicazioni"])


def _normalizza(prefisso: str) -> str:
    """Riduce un prefisso alla forma canonica, rifiutando le risalite.

    I prefissi vanno normalizzati *prima* di salvarli: due regole scritte come
    `foto` e `/foto/` devono essere la stessa regola, altrimenti se ne accumulano
    di duplicate che sembrano diverse e decidono in modo imprevedibile.
    """
    try:
        return str(normalizza_relativo(prefisso)) if prefisso.strip() not in ("", "/") else ""
    except PercorsoNonValido as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


async def _carica(sessione: Sessione, share_id: int) -> Share:
    risultato = await sessione.execute(
        select(Share).where(Share.id == share_id).options(selectinload(Share.rules))
    )
    share = risultato.scalar_one_or_none()
    if share is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pubblicazione non trovata.")
    return share


async def _permessi(sessione: Sessione, share_id: int) -> list[PermessoUtente]:
    risultato = await sessione.execute(
        select(PermessoUtente).where(PermessoUtente.share_id == share_id)
    )
    return list(risultato.scalars().all())


def _regola_out(regola: AccessRule) -> RegolaOut:
    return RegolaOut(
        id=regola.id,
        path_prefix=regola.path_prefix,
        visibility=regola.visibility,
        protetta_da_password=regola.password_hash is not None,
    )


# --- pubblicazioni ---------------------------------------------------------


@router.get("", response_model=list[ShareOut])
async def elenca(sessione: Sessione, _: Amministratore) -> list[Share]:
    risultato = await sessione.execute(select(Share).order_by(Share.label))
    return list(risultato.scalars().all())


@router.post("", response_model=ShareOut, status_code=status.HTTP_201_CREATED)
async def crea(dati: ShareCreate, sessione: Sessione, _: Amministratore) -> Share:
    if await sessione.get(Mount, dati.mount_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La condivisione indicata non esiste.")

    esistente = await sessione.execute(select(Share).where(Share.slug == dati.slug))
    if esistente.scalar_one_or_none() is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Esiste già una pubblicazione {dati.slug!r}."
        )

    share = Share(
        slug=dati.slug,
        label=dati.label,
        description=dati.description,
        mount_id=dati.mount_id,
        subpath=_normalizza(dati.subpath),
        default_visibility=dati.default_visibility,
        is_enabled=dati.is_enabled,
        # Proposti, non imposti: sono le cartelle che i NAS creano per conto
        # proprio, e chi pubblica puo' toglierle dall'elenco se le vuole vedere.
        hidden_patterns=archivio.NASCOSTI_PROPOSTI,
    )
    sessione.add(share)
    await sessione.commit()
    await sessione.refresh(share)
    await scorciatoie.riallinea(sessione)
    return share


@router.get("/{share_id}", response_model=ShareDettaglio)
async def dettaglio(share_id: int, sessione: Sessione, _: Amministratore) -> ShareDettaglio:
    share = await _carica(sessione, share_id)
    dettaglio = ShareDettaglio.model_validate(share)
    dettaglio.regole = [_regola_out(r) for r in share.rules]
    dettaglio.permessi = [
        PermessoOut.model_validate(p) for p in await _permessi(sessione, share_id)
    ]
    return dettaglio


@router.patch("/{share_id}", response_model=ShareOut)
async def modifica(
    share_id: int, dati: ShareUpdate, sessione: Sessione, _: Amministratore
) -> Share:
    share = await _carica(sessione, share_id)

    if dati.slug is not None and dati.slug != share.slug:
        occupato = await sessione.execute(select(Share).where(Share.slug == dati.slug))
        if occupato.scalar_one_or_none() is not None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"Esiste già una pubblicazione {dati.slug!r}."
            )
        share.slug = dati.slug

    if dati.label is not None:
        share.label = dati.label
    if dati.mount_id is not None and dati.mount_id != share.mount_id:
        if await sessione.get(Mount, dati.mount_id) is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "La condivisione indicata non esiste.")
        share.mount_id = dati.mount_id
    if dati.subpath is not None:
        share.subpath = _normalizza(dati.subpath)
    if dati.hidden_patterns is not None:
        share.hidden_patterns = dati.hidden_patterns
    if dati.description is not None:
        share.description = dati.description
    if dati.default_visibility is not None:
        share.default_visibility = dati.default_visibility
    if dati.is_enabled is not None:
        share.is_enabled = dati.is_enabled
    await sessione.commit()
    await sessione.refresh(share)
    # Anche solo spegnere una pubblicazione cambia le scorciatoie: lasciarne
    # una attiva verso una cartella non piu pubblicata darebbe un errore
    # inspiegabile a chi segue un vecchio collegamento.
    await scorciatoie.riallinea(sessione)
    return share


@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def elimina(share_id: int, sessione: Sessione, _: Amministratore) -> None:
    share = await _carica(sessione, share_id)
    await sessione.delete(share)
    await sessione.commit()
    await scorciatoie.riallinea(sessione)


@router.post("/scorciatoie")
async def riapplica_scorciatoie(sessione: Sessione, _: Amministratore) -> dict[str, object]:
    """Riscrive gli indirizzi corti nel web server.

    Vengono gia riscritti a ogni cambiamento. Questo serve quando il web server
    era irraggiungibile in quel momento, o quando la configurazione e stata
    toccata a mano: senza, l'unico modo per rimetterli a posto sarebbe
    modificare una pubblicazione a vuoto.
    """
    return await scorciatoie.riallinea(sessione)


# --- regole di visibilità --------------------------------------------------


@router.post("/{share_id}/regole", response_model=RegolaOut, status_code=status.HTTP_201_CREATED)
async def aggiungi_regola(
    share_id: int, dati: RegolaCreate, sessione: Sessione, _: Amministratore
) -> RegolaOut:
    share = await _carica(sessione, share_id)
    prefisso = _normalizza(dati.path_prefix)

    # Una sola regola per prefisso: due regole sullo stesso percorso
    # renderebbero la decisione dipendente dall'ordine di lettura.
    for esistente in share.rules:
        if esistente.path_prefix == prefisso:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Esiste già una regola per il percorso {prefisso or '(radice)'!r}.",
            )

    regola = AccessRule(
        share_id=share_id,
        path_prefix=prefisso,
        visibility=dati.visibility,
        password_hash=(
            hash_password(dati.password)
            if dati.visibility is Visibilita.PASSWORD and dati.password
            else None
        ),
    )
    sessione.add(regola)
    await sessione.commit()
    await sessione.refresh(regola)
    return _regola_out(regola)


@router.delete("/{share_id}/regole/{regola_id}", status_code=status.HTTP_204_NO_CONTENT)
async def togli_regola(
    share_id: int, regola_id: int, sessione: Sessione, _: Amministratore
) -> None:
    regola = await sessione.get(AccessRule, regola_id)
    if regola is None or regola.share_id != share_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Regola non trovata.")
    await sessione.delete(regola)
    await sessione.commit()


# --- permessi degli utenti -------------------------------------------------


@router.put("/{share_id}/permessi", response_model=PermessoOut, status_code=status.HTTP_200_OK)
async def assegna_permesso(
    share_id: int, dati: PermessoCreate, sessione: Sessione, _: Amministratore
) -> PermessoUtente:
    """Assegna o aggiorna il permesso di un utente su un percorso.

    È una PUT e non una POST perché l'operazione è idempotente: riassegnare lo
    stesso percorso allo stesso utente ne cambia il livello invece di creare un
    secondo permesso che contraddirebbe il primo.
    """
    await _carica(sessione, share_id)
    if await sessione.get(User, dati.user_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "L'utente indicato non esiste.")

    prefisso = _normalizza(dati.path_prefix)
    risultato = await sessione.execute(
        select(PermessoUtente).where(
            PermessoUtente.share_id == share_id,
            PermessoUtente.user_id == dati.user_id,
            PermessoUtente.path_prefix == prefisso,
        )
    )
    permesso = risultato.scalar_one_or_none()
    if permesso is None:
        permesso = PermessoUtente(
            share_id=share_id, user_id=dati.user_id, path_prefix=prefisso, livello=dati.livello
        )
        sessione.add(permesso)
    else:
        permesso.livello = dati.livello

    await sessione.commit()
    await sessione.refresh(permesso)
    return permesso


@router.delete("/{share_id}/permessi/{permesso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def togli_permesso(
    share_id: int, permesso_id: int, sessione: Sessione, _: Amministratore
) -> None:
    permesso = await sessione.get(PermessoUtente, permesso_id)
    if permesso is None or permesso.share_id != share_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Permesso non trovato.")
    await sessione.delete(permesso)
    await sessione.commit()


# --- verifica -------------------------------------------------------------


@router.post("/{share_id}/prova-accesso", response_model=EsitoAccesso)
async def prova_accesso(
    share_id: int, dati: ProvaAccesso, sessione: Sessione, _: Amministratore
) -> EsitoAccesso:
    """Dice se un percorso è accessibile e **quale regola l'ha deciso**.

    Configurare permessi a prefissi senza poterli verificare significa
    scoprire gli errori quando è troppo tardi. Con `user_id` a `None` si prova
    l'accesso anonimo.
    """
    share = await _carica(sessione, share_id)

    utente = None
    if dati.user_id is not None:
        utente = await sessione.get(User, dati.user_id)
        if utente is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "L'utente indicato non esiste.")

    permessi = (
        [p for p in await _permessi(sessione, share_id) if p.user_id == dati.user_id]
        if dati.user_id is not None
        else []
    )

    # Il percorso arriva da fuori: va normalizzato qui, altrimenti una risalita
    # farebbe uscire un errore interno invece di una risposta comprensibile.
    decisione = acl.valuta(share, _normalizza(dati.percorso), utente, permessi=permessi)
    return EsitoAccesso(
        consentito=decisione.consentito,
        scrittura=decisione.scrittura,
        visibilita=decisione.visibilita,
        motivo=decisione.motivo,
        regola=decisione.regola.path_prefix if decisione.regola else None,
        permesso=decisione.permesso.path_prefix if decisione.permesso else None,
    )


# --- link di condivisione --------------------------------------------------


def _link_con_share(collegamento: ShareLink, share: Share) -> LinkOut:
    """Il link come lo vede chi lo amministra.

    `esaurito` non e' un campo del database ma il verdetto delle stesse regole
    che decidono in ingresso: senza, l'elenco mostrerebbe come attivo un link
    scaduto stanotte.
    """
    return LinkOut(
        id=collegamento.id,
        path=collegamento.path,
        label=collegamento.label,
        expires_at=collegamento.expires_at,
        max_downloads=collegamento.max_downloads,
        download_count=collegamento.download_count,
        is_revoked=collegamento.is_revoked,
        protetto_da_password=collegamento.password_hash is not None,
        esaurito=not servizio_link.verifica(collegamento, share, collegamento.path).valido,
    )


@router.get("/{share_id}/link", response_model=list[LinkOut])
async def elenca_link(share_id: int, sessione: Sessione, _: Amministratore) -> list[LinkOut]:
    share = await _carica(sessione, share_id)
    risultato = await sessione.execute(
        select(ShareLink).where(ShareLink.share_id == share_id).order_by(ShareLink.id.desc())
    )
    return [_link_con_share(c, share) for c in risultato.scalars().all()]


@router.post("/{share_id}/link", response_model=LinkCreato, status_code=status.HTTP_201_CREATED)
async def crea_link(
    share_id: int, dati: LinkCreate, sessione: Sessione, amministratore: Amministratore
) -> LinkCreato:
    """Crea un link di condivisione e ne restituisce il token **una sola volta**.

    Nel database finisce solo l'impronta del token: se qualcuno legge il
    database non ricava i link attivi, ma nemmeno noi possiamo mostrarlo di
    nuovo dopo. Chi lo crea deve copiarlo adesso.
    """
    share = await _carica(sessione, share_id)
    token = servizio_link.nuovo_token()

    collegamento = ShareLink(
        share_id=share_id,
        created_by=amministratore.id,
        token_hash=servizio_link.impronta(token),
        path=_normalizza(dati.percorso),
        label=dati.etichetta,
        password_hash=hash_password(dati.password) if dati.password else None,
        expires_at=(
            datetime.now(UTC) + timedelta(days=dati.giorni) if dati.giorni is not None else None
        ),
        max_downloads=dati.max_download,
    )
    sessione.add(collegamento)
    await sessione.commit()
    await sessione.refresh(collegamento)

    base = _link_con_share(collegamento, share)
    return LinkCreato(**base.model_dump(), token=token)


@router.delete("/{share_id}/link/{link_id}", response_model=LinkOut)
async def revoca_link(
    share_id: int, link_id: int, sessione: Sessione, _: Amministratore
) -> LinkOut:
    """Revoca un link senza cancellarlo.

    La riga resta: quante volte e' stato usato un collegamento poi revocato e'
    esattamente cio' che si vuole sapere dopo averlo revocato.
    """
    share = await _carica(sessione, share_id)
    collegamento = await sessione.get(ShareLink, link_id)
    if collegamento is None or collegamento.share_id != share_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collegamento non trovato.")

    collegamento.is_revoked = True
    await sessione.commit()
    await sessione.refresh(collegamento)
    return _link_con_share(collegamento, share)
