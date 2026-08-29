"""Hash delle password e token di accesso."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import get_settings

#: Argon2id con i parametri predefiniti della libreria, che sono quelli
#: raccomandati e vengono aggiornati dai manutentori nel tempo.
_hasher = PasswordHasher()

ALGORITMO = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verifica_password(password: str, hash_memorizzato: str) -> bool:
    try:
        _hasher.verify(hash_memorizzato, password)
    except VerifyMismatchError, InvalidHashError:
        return False
    return True


def hash_da_rigenerare(hash_memorizzato: str) -> bool:
    """Vero se l'hash usa parametri superati e va ricalcolato al prossimo accesso."""
    try:
        return _hasher.check_needs_rehash(hash_memorizzato)
    except InvalidHashError:
        return True


def crea_access_token(subject: str, *, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    adesso = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": adesso,
        "exp": adesso + timedelta(minutes=settings.access_token_minutes),
        "typ": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITMO)


def decodifica_token(token: str) -> dict[str, Any] | None:
    """Restituisce il contenuto del token, o None se non e valido o e scaduto."""
    try:
        return jwt.decode(
            token,
            get_settings().secret_key,
            algorithms=[ALGORITMO],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        return None


def crea_gettone_percorso(share_id: int, percorso: str, *, minuti: int = 5) -> str:
    """Autorizzazione a vita breve per scaricare un percorso preciso.

    Serve perche' un download e' una navigazione del browser, non una chiamata
    fatta dal codice: non puo' portare intestazioni, e quindi non puo' portare
    il token di sessione. L'alternativa sarebbe mettere la password nella query
    string, dove finirebbe nei log del web server e nella cronologia.

    Il gettone vale per *quel* percorso di *quella* pubblicazione e per pochi
    minuti: se anche venisse intercettato non aprirebbe nient'altro.
    """
    settings = get_settings()
    adesso = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": f"archivio:{share_id}",
        "pth": percorso,
        "iat": adesso,
        "exp": adesso + timedelta(minutes=minuti),
        "typ": "archivio",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITMO)


def verifica_gettone_percorso(gettone: str, share_id: int, percorso: str) -> bool:
    """Vero se il gettone autorizza proprio questo percorso di questa pubblicazione."""
    contenuto = decodifica_token(gettone)
    if contenuto is None or contenuto.get("typ") != "archivio":
        return False
    return contenuto.get("sub") == f"archivio:{share_id}" and contenuto.get("pth") == percorso
