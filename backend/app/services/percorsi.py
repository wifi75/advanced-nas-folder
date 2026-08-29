"""Risoluzione sicura dei percorsi dentro uno share.

Ogni percorso che arriva da una richiesta HTTP passa di qui. È la barriera che
impedisce a `../../etc/passwd` di diventare un file servito: senza, un pannello
che pubblica cartelle diventa un modo per leggere l'intero disco.

Il principio è lo stesso dei validatori dell'agent: si costruisce il percorso
finale a partire dalla radice e si verifica che non ne sia uscito, invece di
cercare di riconoscere le sequenze pericolose una per una.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path, PurePosixPath


class PercorsoNonValido(ValueError):
    """Il percorso richiesto è malformato o tenta di uscire dallo share."""


#: Caratteri che non possono comparire in un percorso richiesto.
#: Il byte nullo tronca le stringhe nelle chiamate di sistema sottostanti.
_VIETATI = ("\x00", "\r", "\n")


def normalizza_relativo(percorso: str | None) -> PurePosixPath:
    """Riduce un percorso richiesto alla sua forma canonica relativa.

    Rifiuta risalite e percorsi assoluti. Non tocca il filesystem: serve a
    ottenere un percorso di cui ci si possa fidare *prima* di usarlo.
    """
    if percorso is None or percorso.strip() in ("", "/"):
        return PurePosixPath()

    if any(c in percorso for c in _VIETATI):
        raise PercorsoNonValido("Il percorso contiene caratteri non ammessi.")

    # Le forme Unicode composte e decomposte danno lo stesso nome a schermo ma
    # stringhe diverse: normalizzarle evita che due regole di accesso
    # apparentemente uguali si comportino in modo diverso.
    percorso = unicodedata.normalize("NFC", percorso)

    parti: list[str] = []
    for pezzo in percorso.replace("\\", "/").split("/"):
        if pezzo in ("", "."):
            continue
        if pezzo == "..":
            # Non si risale nemmeno di un livello che verrebbe poi ridisceso:
            # il percorso richiesto è sempre relativo alla radice dello share.
            raise PercorsoNonValido("Il percorso non può contenere '..'.")
        parti.append(pezzo)

    return PurePosixPath(*parti)


def risolvi(radice: Path, percorso: str | None) -> Path:
    """Percorso assoluto e reale corrispondente alla richiesta.

    Segue i collegamenti simbolici e verifica che la destinazione sia comunque
    dentro la radice: un collegamento dentro la cartella condivisa che punta
    fuori è il modo più semplice per aggirare un controllo fatto solo sulla
    stringa. Il controllo va quindi fatto sul percorso risolto, non su quello
    richiesto.
    """
    relativo = normalizza_relativo(percorso)

    radice_reale = radice.resolve(strict=False)
    candidato = (radice_reale / relativo).resolve(strict=False)

    if candidato != radice_reale and radice_reale not in candidato.parents:
        raise PercorsoNonValido("Il percorso esce dalla cartella pubblicata.")

    return candidato


def dentro(radice: Path, percorso: Path) -> bool:
    """Vero se `percorso` è la radice stessa o è contenuto in essa."""
    radice_reale = radice.resolve(strict=False)
    reale = percorso.resolve(strict=False)
    return reale == radice_reale or radice_reale in reale.parents


def e_nascosto(relativo: PurePosixPath) -> bool:
    """Vero se una qualunque parte del percorso inizia con un punto."""
    return any(parte.startswith(".") for parte in relativo.parts)
