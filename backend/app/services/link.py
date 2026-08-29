"""Link di condivisione: creazione, validità e consumo.

Un link è un modo per far arrivare una cartella a chi non ha un account e non
lo avrà mai — il classico «mandami quel file». Per questo non passa dai
permessi degli utenti: **il token stesso è l'autorizzazione**, limitata a un
ramo, a una scadenza e a un numero di scaricamenti.

Restano due limiti che il token non supera, perché non sarebbero più
eccezioni ma buchi: non porta mai fuori dal ramo per cui è stato creato, e non
apre un percorso marcato *negato*, che resta chiuso a chiunque.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from app.models import Share, ShareLink
from app.models.enums import Visibilita
from app.services import acl
from app.services.percorsi import normalizza_relativo

#: 32 byte di casualità: il token è l'unica cosa che protegge il contenuto, e
#: viene provato da chiunque conosca l'indirizzo del pannello.
_BYTE_TOKEN = 32


def nuovo_token() -> str:
    return secrets.token_urlsafe(_BYTE_TOKEN)


def impronta(token: str) -> str:
    """Impronta con cui il token viene memorizzato.

    SHA-256 e non Argon2: quest'ultimo protegge i segreti *indovinabili*, e una
    password lo è. Un token da 32 byte casuali non lo è, e pagare un hash lento
    a ogni richiesta di ogni file servirebbe solo a rallentare i download.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class EsitoLink:
    valido: bool
    motivo: str


def _scaduto(link: ShareLink, adesso: datetime) -> bool:
    if link.expires_at is None:
        return False
    scadenza = link.expires_at
    # SQLite restituisce date senza fuso: interpretarle come UTC, che è come
    # sono state scritte. Senza, il confronto solleva un errore invece di dare
    # una risposta.
    if scadenza.tzinfo is None:
        scadenza = scadenza.replace(tzinfo=UTC)
    return scadenza <= adesso


def esaurito(link: ShareLink) -> bool:
    return link.max_downloads is not None and link.download_count >= link.max_downloads


def dentro_ramo(link: ShareLink, percorso: str | None) -> bool:
    """Vero se il percorso è il ramo del link o una sua sottocartella.

    Confronto per componenti e non per stringhe: `foto` non deve corrispondere
    a `fotografie`.
    """
    ramo = normalizza_relativo(link.path).parts
    richiesto = normalizza_relativo(percorso).parts
    return richiesto[: len(ramo)] == ramo


def verifica(
    link: ShareLink,
    share: Share,
    percorso: str | None,
    *,
    adesso: datetime | None = None,
) -> EsitoLink:
    """Dice se il link apre questo percorso, e altrimenti perché no."""
    adesso = adesso or datetime.now(UTC)

    if link.is_revoked:
        return EsitoLink(False, "Questo collegamento è stato revocato.")
    if _scaduto(link, adesso):
        return EsitoLink(False, "Questo collegamento è scaduto.")
    if esaurito(link):
        return EsitoLink(False, "Questo collegamento ha raggiunto il limite di scaricamenti.")
    if not share.is_enabled:
        return EsitoLink(False, "La pubblicazione non è più disponibile.")
    if not dentro_ramo(link, percorso):
        return EsitoLink(False, "Il collegamento non copre questo percorso.")

    # Il divieto esplicito vale anche qui: se valesse solo per gli utenti
    # registrati, creare un link sarebbe il modo per aggirarlo.
    regola = acl.regola_applicabile(share, percorso)
    if regola is not None and regola.visibility is Visibilita.NEGATA:
        return EsitoLink(False, "Accesso negato da una regola del percorso.")

    return EsitoLink(True, "Collegamento valido.")
