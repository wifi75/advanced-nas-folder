"""Permessi di accesso per sottocartella.

Due livelli, che rispondono a domande diverse:

* la **visibilità del percorso** dice chi in generale può vederlo — chiunque
  senza accedere (accesso anonimo), chi ha la password, qualunque utente
  autenticato, solo chi ha un permesso esplicito, o nessuno;
* il **permesso del singolo utente** dice cosa può fare *quella* persona su
  *quel* percorso, e sovrascrive la visibilità.

In entrambi **vince la regola con il prefisso più lungo** che corrisponde, così
una sottocartella può essere più restrittiva della cartella che la contiene —
o più permissiva, se è quello che si vuole.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath

from app.models import AccessRule, PermessoUtente, Share, User
from app.models.enums import Livello, Visibilita
from app.services.percorsi import normalizza_relativo


@dataclass(frozen=True, slots=True)
class Decisione:
    consentito: bool
    #: Vero se l'utente può anche modificare, non solo leggere.
    scrittura: bool
    visibilita: Visibilita
    #: Regola di visibilità che ha deciso, se ce n'è una.
    regola: AccessRule | None
    #: Permesso personale che ha deciso, se ce n'è uno.
    permesso: PermessoUtente | None
    motivo: str


def _corrisponde(prefisso: str, percorso: PurePosixPath) -> bool:
    """Vero se `prefisso` è il percorso stesso o una sua cartella superiore.

    Il confronto è per componenti e non per stringhe: `foto` non deve
    corrispondere a `fotografie`, che con un semplice `startswith` accadrebbe.
    """
    parti = normalizza_relativo(prefisso).parts
    if not parti:
        return True
    return percorso.parts[: len(parti)] == parti


def _piu_specifico[T](candidati: Iterable[T], prefisso_di: Callable[[T], str]) -> T | None:
    """Fra i candidati, quello con il prefisso composto da più cartelle."""
    scelti = list(candidati)
    if not scelti:
        return None
    return max(scelti, key=lambda c: len(normalizza_relativo(prefisso_di(c)).parts))


def regola_applicabile(share: Share, percorso: str | None) -> AccessRule | None:
    """La regola di visibilità più specifica che copre il percorso richiesto."""
    richiesto = normalizza_relativo(percorso)
    return _piu_specifico(
        (r for r in share.rules if _corrisponde(r.path_prefix, richiesto)),
        lambda r: r.path_prefix,
    )


def permesso_applicabile(
    permessi: Sequence[PermessoUtente], percorso: str | None
) -> PermessoUtente | None:
    """Il permesso personale più specifico che copre il percorso richiesto."""
    richiesto = normalizza_relativo(percorso)
    return _piu_specifico(
        (p for p in permessi if _corrisponde(p.path_prefix, richiesto)),
        lambda p: p.path_prefix,
    )


def valuta(
    share: Share,
    percorso: str | None,
    utente: User | None,
    *,
    permessi: Sequence[PermessoUtente] = (),
    password_fornita: bool = False,
) -> Decisione:
    """Decide se l'accesso è consentito, e spiega perché.

    `permessi` sono i permessi personali dell'utente su questo share, già
    caricati dal chiamante. `password_fornita` indica che la verifica della
    password è già stata superata: qui si prende solo la decisione.
    """
    if not share.is_enabled:
        return Decisione(
            False, False, Visibilita.NEGATA, None, None, "La pubblicazione è disattivata."
        )

    regola = regola_applicabile(share, percorso)
    visibilita = regola.visibility if regola is not None else share.default_visibility

    # Un percorso marcato "negato" resta chiuso a chiunque, amministratore
    # incluso: altrimenti quella visibilità non significherebbe nulla.
    if visibilita is Visibilita.NEGATA:
        return Decisione(
            False, False, visibilita, regola, None, "Accesso negato da una regola del percorso."
        )

    if utente is not None and utente.is_admin:
        return Decisione(True, True, visibilita, regola, None, "Amministratore.")

    # Il permesso personale viene prima della visibilità: è il modo per dire
    # "questa cartella la vede solo Mario", e anche per togliere a una persona
    # un ramo che per gli altri resta aperto.
    permesso = permesso_applicabile(permessi, percorso) if utente is not None else None
    if permesso is not None:
        if permesso.livello is Livello.NEGATO:
            return Decisione(
                False, False, visibilita, regola, permesso, "Accesso negato a questo utente."
            )
        return Decisione(
            True,
            permesso.livello is Livello.SCRITTURA,
            visibilita,
            regola,
            permesso,
            "Permesso assegnato all'utente.",
        )

    match visibilita:
        case Visibilita.PUBBLICA:
            return Decisione(True, False, visibilita, regola, None, "Percorso pubblico.")
        case Visibilita.UTENTI:
            if utente is None:
                return Decisione(
                    False, False, visibilita, regola, None, "Serve l'accesso al pannello."
                )
            return Decisione(True, False, visibilita, regola, None, "Utente autenticato.")
        case Visibilita.UTENTI_SCELTI:
            # Nessun permesso personale corrispondente: qui l'assenza è un no.
            return Decisione(
                False,
                False,
                visibilita,
                regola,
                None,
                "Riservato agli utenti autorizzati su questo percorso.",
            )
        case Visibilita.PASSWORD:
            if password_fornita:
                return Decisione(True, False, visibilita, regola, None, "Password corretta.")
            return Decisione(False, False, visibilita, regola, None, "Serve la password.")

    return Decisione(False, False, Visibilita.NEGATA, regola, None, "Visibilità non riconosciuta.")


def dentro_ambito(utente: User | None, percorso: str | None) -> bool:
    """Vero se il percorso rientra nell'ambito assegnato all'utente.

    L'ambito limita un utente a un ramo dello share, indipendentemente dai
    permessi: è un confine, non un permesso. Il confronto è per componenti.
    """
    if utente is None or not utente.scope or utente.is_admin:
        return True
    ambito = normalizza_relativo(utente.scope).parts
    richiesto = normalizza_relativo(percorso).parts
    return richiesto[: len(ambito)] == ambito
