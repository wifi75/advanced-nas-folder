"""Dipendenze condivise dagli endpoint."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import decodifica_token
from app.models import User

Sessione = Annotated[AsyncSession, Depends(get_session)]

_bearer = HTTPBearer(auto_error=False)
Credenziali = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]

_NON_AUTENTICATO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Sessione non valida o scaduta. Accedi di nuovo.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def utente_corrente(credenziali: Credenziali, sessione: Sessione) -> User:
    if credenziali is None:
        raise _NON_AUTENTICATO

    contenuto = decodifica_token(credenziali.credentials)
    if contenuto is None:
        raise _NON_AUTENTICATO

    try:
        user_id = int(contenuto["sub"])
    except KeyError, TypeError, ValueError:
        raise _NON_AUTENTICATO from None

    utente = await sessione.get(User, user_id)
    if utente is None or not utente.is_active:
        # Stesso errore dell'utente inesistente: distinguere "disattivato" da
        # "inesistente" direbbe a chi prova quali account esistono.
        raise _NON_AUTENTICATO
    return utente


UtenteCorrente = Annotated[User, Depends(utente_corrente)]


async def utente_facoltativo(credenziali: Credenziali, sessione: Sessione) -> User | None:
    """L'utente, se ha effettuato l'accesso; `None` altrimenti.

    Serve agli endpoint che devono funzionare anche per chi non ha un account:
    una cartella pubblicata come pubblica si scarica senza accedere, e
    pretendere un token la renderebbe pubblica solo di nome.

    Un token presente ma non valido resta un errore: chi lo invia crede di
    essere autenticato, e trattarlo come anonimo gli mostrerebbe in silenzio
    meno di quanto gli spetta.
    """
    if credenziali is None:
        return None
    return await utente_corrente(credenziali, sessione)


UtenteFacoltativo = Annotated[User | None, Depends(utente_facoltativo)]


async def amministratore(utente: UtenteCorrente) -> User:
    if not utente.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Questa operazione richiede i permessi di amministratore.",
        )
    return utente


Amministratore = Annotated[User, Depends(amministratore)]


async def cerca_utente(sessione: AsyncSession, username: str) -> User | None:
    risultato = await sessione.execute(select(User).where(User.username == username))
    return risultato.scalar_one_or_none()
