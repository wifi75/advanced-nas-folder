"""Accesso al pannello."""

import asyncio
import secrets

from fastapi import APIRouter, HTTPException, status

from app.api.deps import Sessione, UtenteCorrente, cerca_utente
from app.core.config import get_settings
from app.core.security import crea_access_token, hash_password, verifica_password
from app.schemas.auth import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["autenticazione"])

#: Password iniziale dell'amministratore creato dall'installazione. Serve solo
#: a segnalare nel pannello che va cambiata, non a consentire l'accesso.
PASSWORD_INIZIALE = "admin"  # noqa: S105

_CREDENZIALI_ERRATE = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Nome utente o password non corretti.",
)


@router.post("/login", response_model=TokenResponse)
async def login(dati: LoginRequest, sessione: Sessione) -> TokenResponse:
    utente = await cerca_utente(sessione, dati.username)

    if utente is None:
        # Verifica comunque un hash fittizio: senza, rispondere subito rivelerebbe
        # quali nomi utente esistono misurando il tempo di risposta.
        hash_password(secrets.token_urlsafe(16))
        raise _CREDENZIALI_ERRATE

    if not verifica_password(dati.password, utente.password_hash):
        # Ritardo minimo contro i tentativi automatici a raffica.
        await asyncio.sleep(0.3)
        raise _CREDENZIALI_ERRATE

    if not utente.is_active:
        raise _CREDENZIALI_ERRATE

    settings = get_settings()
    return TokenResponse(
        access_token=crea_access_token(str(utente.id), extra={"adm": utente.is_admin}),
        expires_in=settings.access_token_minutes * 60,
        user=UserOut.model_validate(utente),
        password_predefinita=verifica_password(PASSWORD_INIZIALE, utente.password_hash),
    )


@router.get("/me", response_model=UserOut)
async def me(utente: UtenteCorrente) -> UserOut:
    return UserOut.model_validate(utente)
