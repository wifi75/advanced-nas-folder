"""Gestione degli utenti.

Senza questa parte i permessi per utente restano una funzione teorica: si
possono assegnare cartelle a un utente, ma l'unico utente esistente è
l'amministratore creato dall'installazione.

Due protezioni valgono per tutte le operazioni, e sono la ragione per cui
questo file non è un CRUD qualunque:

* **non ci si può chiudere fuori.** Togliersi i privilegi, disattivarsi o
  cancellarsi lascerebbe un pannello che gestisce mount di rete senza nessuno
  che possa amministrarlo;
* **l'ultimo amministratore non si tocca.** Vale anche quando a farlo è un
  altro amministratore: il risultato sarebbe lo stesso, un impianto ingestibile
  senza rimettere le mani nel database.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import Amministratore, Sessione, UtenteCorrente
from app.core.security import hash_password, verifica_password
from app.models import User
from app.schemas.auth import CambioPassword, UserAdminOut, UserCreate, UserUpdate
from app.services.percorsi import PercorsoNonValido, normalizza_relativo

router = APIRouter(prefix="/utenti", tags=["utenti"])


async def _quanti_amministratori(sessione: Sessione) -> int:
    risultato = await sessione.execute(
        select(func.count())
        .select_from(User)
        .where(User.is_admin.is_(True), User.is_active.is_(True))
    )
    return int(risultato.scalar_one())


async def _carica(sessione: Sessione, user_id: int) -> User:
    utente = await sessione.get(User, user_id)
    if utente is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utente non trovato.")
    return utente


def _ambito(valore: str) -> str:
    """Riduce l'ambito alla forma canonica, rifiutando le risalite.

    L'ambito è un confine, non un permesso: se lo si potesse scrivere come
    `../..` smetterebbe di esserlo.
    """
    if valore.strip() in ("", "/"):
        return ""
    try:
        return str(normalizza_relativo(valore))
    except PercorsoNonValido as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


async def _resterebbe_senza_amministratori(
    sessione: Sessione, utente: User, *, admin: bool | None, attivo: bool | None
) -> bool:
    """Vero se la modifica lascerebbe il pannello senza amministratori attivi."""
    perde_i_privilegi = utente.is_admin and (admin is False or attivo is False)
    if not perde_i_privilegi:
        return False
    return await _quanti_amministratori(sessione) <= 1


@router.get("", response_model=list[UserAdminOut])
async def elenca(sessione: Sessione, _: Amministratore) -> list[User]:
    risultato = await sessione.execute(select(User).order_by(User.username))
    return list(risultato.scalars().all())


@router.post("", response_model=UserAdminOut, status_code=status.HTTP_201_CREATED)
async def crea(dati: UserCreate, sessione: Sessione, _: Amministratore) -> User:
    esistente = await sessione.execute(select(User).where(User.username == dati.username))
    if esistente.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"L'utente {dati.username!r} esiste già.")

    utente = User(
        username=dati.username,
        email=dati.email or None,
        password_hash=hash_password(dati.password),
        is_admin=dati.is_admin,
        is_active=True,
        scope=_ambito(dati.scope),
        can_create=dati.can_create,
        can_delete=dati.can_delete,
        can_modify=dati.can_modify,
        can_rename=dati.can_rename,
        can_share=dati.can_share,
        can_download=dati.can_download,
        can_upload=dati.can_upload,
    )
    sessione.add(utente)
    await sessione.commit()
    await sessione.refresh(utente)
    return utente


@router.patch("/{user_id}", response_model=UserAdminOut)
async def modifica(
    user_id: int, dati: UserUpdate, sessione: Sessione, amministratore: Amministratore
) -> User:
    utente = await _carica(sessione, user_id)

    if utente.id == amministratore.id and (dati.is_admin is False or dati.is_active is False):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Non puoi togliere i privilegi a te stesso: resteresti fuori dal pannello.",
        )
    if await _resterebbe_senza_amministratori(
        sessione, utente, admin=dati.is_admin, attivo=dati.is_active
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "È l'ultimo amministratore attivo: senza di lui il pannello non sarebbe più "
            "amministrabile.",
        )

    if dati.password is not None:
        utente.password_hash = hash_password(dati.password)
    if dati.email is not None:
        utente.email = dati.email or None
    if dati.scope is not None:
        utente.scope = _ambito(dati.scope)

    for campo in (
        "is_admin",
        "is_active",
        "can_create",
        "can_delete",
        "can_modify",
        "can_rename",
        "can_share",
        "can_download",
        "can_upload",
    ):
        valore = getattr(dati, campo)
        if valore is not None:
            setattr(utente, campo, valore)

    await sessione.commit()
    await sessione.refresh(utente)
    return utente


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def elimina(user_id: int, sessione: Sessione, amministratore: Amministratore) -> None:
    utente = await _carica(sessione, user_id)

    if utente.id == amministratore.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Non puoi eliminare te stesso.")
    if utente.is_admin and await _quanti_amministratori(sessione) <= 1:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "È l'ultimo amministratore attivo: eliminarlo renderebbe il pannello ingestibile.",
        )

    # I permessi assegnati all'utente se ne vanno con lui: la chiave esterna ha
    # ondelete CASCADE, quindi non restano righe che puntano a un utente morto.
    await sessione.delete(utente)
    await sessione.commit()


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def cambia_la_mia_password(
    dati: CambioPassword, sessione: Sessione, utente: UtenteCorrente
) -> None:
    """Cambio della propria password.

    Richiede quella attuale anche se si è già autenticati: un token rubato non
    deve bastare a chiudere fuori il proprietario dell'account.
    """
    if not verifica_password(dati.attuale, utente.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La password attuale non è corretta.")

    utente.password_hash = hash_password(dati.nuova)
    await sessione.commit()
