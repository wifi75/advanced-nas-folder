"""Download di una cartella come archivio ZIP.

Lo ZIP viene prodotto **mentre lo si invia**, non costruito prima su disco:
una cartella del NAS puo' pesare piu' dello spazio libero della macchina che
serve il pannello, e comunque far aspettare qualche minuto prima che il
download cominci e' il modo piu' semplice per far credere che non funzioni.

Il prezzo di questa scelta e' che la dimensione totale non e' nota in
anticipo: il browser mostra un download senza percentuale. Sapere subito
quanto manca vale meno che poter scaricare la cartella.

I file vengono inseriti **senza compressione**. Su un NAS domestico il
contenuto e' quasi sempre gia' compresso — foto, video, archivi — e
comprimerlo di nuovo consuma processore per guadagnare qualche per mille.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from pathlib import Path, PurePosixPath

from zipstream import ZIP_STORED, ZipStream

#: Come per la ricerca, un tetto alle cartelle visitate: senza, una cartella
#: con un collegamento circolare produrrebbe uno ZIP infinito.
MAX_CARTELLE = 5000


def _raccogli(
    radice: Path, base: PurePosixPath, consentito: Callable[[str], bool]
) -> list[tuple[Path, str]]:
    """Elenca i file da mettere nell'archivio, con il nome che avranno dentro.

    Ogni file passa dal controllo degli accessi: una cartella vietata non deve
    finire nello ZIP solo perche' e' dentro una che si puo' scaricare.
    """
    dentro: list[tuple[Path, str]] = []
    da_visitare: list[tuple[Path, PurePosixPath]] = [(radice, PurePosixPath())]
    viste = 0

    while da_visitare and viste < MAX_CARTELLE:
        cartella, relativo = da_visitare.pop()
        viste += 1

        try:
            elementi = list(os.scandir(cartella))
        except OSError:
            continue

        for elemento in elementi:
            if elemento.name.startswith("."):
                continue

            interno = relativo / elemento.name
            if not consentito(str(base / interno)):
                continue

            try:
                if elemento.is_dir():
                    da_visitare.append((Path(elemento.path), interno))
                elif elemento.is_file():
                    dentro.append((Path(elemento.path), str(interno)))
            except OSError:
                continue

    dentro.sort(key=lambda voce: voce[1])
    return dentro


def prepara(
    radice: Path, percorso: str, consentito: Callable[[str], bool]
) -> tuple[Iterator[bytes], str]:
    """Restituisce il flusso dello ZIP e il nome del file da proporre."""
    base = PurePosixPath(percorso) if percorso else PurePosixPath()
    file = _raccogli(radice, base, consentito)

    flusso = ZipStream(compress_type=ZIP_STORED)
    for reale, interno in file:
        flusso.add_path(reale, arcname=interno)

    nome = (base.name or "archivio") + ".zip"
    return iter(flusso), nome
