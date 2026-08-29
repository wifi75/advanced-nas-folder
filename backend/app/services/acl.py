"""Permessi di accesso per sottocartella.

Il modello è a prefissi: uno share ha una visibilità predefinita, e ogni regola
la sovrascrive per un ramo dell'albero. **Vince la regola con il prefisso più
lungo che corrisponde**, così una sottocartella può essere più restrittiva
della cartella che la contiene — che è esattamente il requisito del progetto.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from app.models import AccessRule, Share, User
from app.models.enums import Visibilita
from app.services.percorsi import normalizza_relativo


@dataclass(frozen=True, slots=True)
class Decisione:
    consentito: bool
    visibilita: Visibilita
    #: Regola che ha deciso, per poterlo spiegare nel pannello.
    regola: AccessRule | None
    motivo: str


def _prefisso_corrisponde(prefisso: str, percorso: PurePosixPath) -> bool:
    """Vero se `prefisso` è il percorso stesso o una sua cartella superiore.

    Il confronto è per componenti e non per stringhe: `foto` non deve
    corrispondere a `fotografie`, che con un semplice `startswith` accadrebbe.
    """
    parti_prefisso = normalizza_relativo(prefisso).parts
    if not parti_prefisso:
        return True
    return percorso.parts[: len(parti_prefisso)] == parti_prefisso


def regola_applicabile(share: Share, percorso: str | None) -> AccessRule | None:
    """La regola più specifica che copre il percorso richiesto."""
    richiesto = normalizza_relativo(percorso)
    candidate = [r for r in share.rules if _prefisso_corrisponde(r.path_prefix, richiesto)]
    if not candidate:
        return None
    return max(candidate, key=lambda r: len(normalizza_relativo(r.path_prefix).parts))


def valuta(
    share: Share,
    percorso: str | None,
    utente: User | None,
    *,
    password_fornita: bool = False,
) -> Decisione:
    """Decide se l'accesso è consentito, e spiega perché.

    `password_fornita` indica che il richiedente ha già superato la verifica
    della password per questo percorso: la verifica vera avviene altrove, qui
    si prende solo la decisione.
    """
    if not share.is_enabled:
        return Decisione(False, Visibilita.NEGATA, None, "La pubblicazione è disattivata.")

    regola = regola_applicabile(share, percorso)
    visibilita = regola.visibility if regola is not None else share.default_visibility

    # Un amministratore vede tutto, tranne ciò che è esplicitamente negato:
    # una cartella marcata "negata" resta chiusa anche a lui, altrimenti quella
    # visibilità non significherebbe nulla.
    if visibilita is Visibilita.NEGATA:
        return Decisione(False, visibilita, regola, "Accesso negato da una regola.")

    if utente is not None and utente.is_admin:
        return Decisione(True, visibilita, regola, "Amministratore.")

    match visibilita:
        case Visibilita.PUBBLICA:
            return Decisione(True, visibilita, regola, "Percorso pubblico.")
        case Visibilita.UTENTI:
            if utente is None:
                return Decisione(False, visibilita, regola, "Serve l'accesso al pannello.")
            return Decisione(True, visibilita, regola, "Utente autenticato.")
        case Visibilita.PASSWORD:
            if password_fornita:
                return Decisione(True, visibilita, regola, "Password corretta.")
            return Decisione(False, visibilita, regola, "Serve la password.")

    return Decisione(False, Visibilita.NEGATA, regola, "Visibilità non riconosciuta.")


def dentro_ambito(utente: User | None, percorso: str | None) -> bool:
    """Vero se il percorso rientra nell'ambito assegnato all'utente.

    L'ambito limita un utente a un ramo dello share. Il confronto è per
    componenti, non per stringhe, per lo stesso motivo dei prefissi.
    """
    if utente is None or not utente.scope:
        return True
    if utente.is_admin:
        return True
    ambito = normalizza_relativo(utente.scope).parts
    richiesto = normalizza_relativo(percorso).parts
    return richiesto[: len(ambito)] == ambito
