"""Ricerca dei file dentro una cartella pubblicata.

La ricerca attraversa l'albero, e su NFS attraversare un albero costa: ogni
cartella e' un giro di rete. Per questo ci sono due limiti che non sono
opzioni ma parte del progetto — un tetto ai risultati e uno alle cartelle
visitate. Senza, una ricerca su una radice con centomila file terrebbe
occupato un thread per minuti e restituirebbe un elenco che nessuno legge.

Come l'elenco di una cartella, anche i risultati passano dal controllo degli
accessi voce per voce: una ricerca che mostrasse i nomi dei file dentro una
cartella vietata sarebbe un modo di leggerne il contenuto.
"""

from __future__ import annotations

import os
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

import anyio

#: Oltre questo numero di risultati ci si ferma. Chi cerca qualcosa di preciso
#: non arriva mai al duecentesimo risultato: se ci arriva, deve affinare.
MAX_RISULTATI = 200

#: Tetto alle cartelle visitate, per non trasformare una ricerca in una
#: scansione dell'intero NAS.
MAX_CARTELLE = 2000


@dataclass(frozen=True, slots=True)
class Trovato:
    nome: str
    percorso: str
    cartella: bool
    dimensione: int | None
    modificato: datetime | None


def _normalizza(testo: str) -> str:
    """Forma con cui si confrontano i nomi.

    Minuscolo e senza distinzione fra forme Unicode composte e decomposte:
    «città» digitato sulla tastiera e «città» salvato da un Mac sono la stessa
    parola, ma stringhe diverse.
    """
    return unicodedata.normalize("NFC", testo).casefold()


def _cerca_sincrono(
    radice: Path, base: PurePosixPath, termine: str, consentito: Callable[[str], bool]
) -> tuple[list[Trovato], bool]:
    """Percorre l'albero. Sincrona: la chiama un thread separato.

    Restituisce anche se si e' fermata per aver raggiunto un limite: dirlo
    all'utente e' l'unico modo perche' capisca che l'elenco non e' completo.
    """
    ago = _normalizza(termine)
    risultati: list[Trovato] = []
    cartelle_viste = 0
    troncato = False

    da_visitare: list[tuple[Path, PurePosixPath]] = [(radice, base)]

    while da_visitare:
        if len(risultati) >= MAX_RISULTATI or cartelle_viste >= MAX_CARTELLE:
            troncato = True
            break

        cartella, relativo = da_visitare.pop()
        cartelle_viste += 1

        try:
            elementi = list(os.scandir(cartella))
        except OSError:
            # Una cartella illeggibile non deve far fallire la ricerca: si
            # salta, e le altre restano cercabili.
            continue

        for elemento in elementi:
            if elemento.name.startswith("."):
                continue

            percorso = relativo / elemento.name
            if not consentito(str(percorso)):
                continue

            try:
                e_cartella = elemento.is_dir()
                info = elemento.stat()
            except OSError:
                continue

            if e_cartella:
                da_visitare.append((Path(elemento.path), percorso))

            if ago in _normalizza(elemento.name):
                risultati.append(
                    Trovato(
                        nome=elemento.name,
                        percorso=str(percorso),
                        cartella=e_cartella,
                        dimensione=None if e_cartella else info.st_size,
                        modificato=datetime.fromtimestamp(info.st_mtime, UTC),
                    )
                )
                if len(risultati) >= MAX_RISULTATI:
                    troncato = True
                    break

    risultati.sort(key=lambda r: (not r.cartella, r.percorso.casefold()))
    return risultati, troncato


async def cerca(
    radice: Path, percorso: str, termine: str, consentito: Callable[[str], bool]
) -> tuple[list[Trovato], bool]:
    """Cerca `termine` nei nomi, sotto `percorso`."""
    base = PurePosixPath(percorso) if percorso else PurePosixPath()
    return await anyio.to_thread.run_sync(_cerca_sincrono, radice, base, termine, consentito)
