"""Miniature delle immagini pubblicate.

Perché non basta rimpicciolire nel browser: una cartella di foto del NAS pesa
gigabyte, e una galleria che scarica ogni scatto per intero solo per mostrarlo
a 150 pixel satura la rete e fa sembrare il pannello rotto. Qui l'immagine
viene ridotta **sul server**, una volta, e poi riusata.

La miniatura prodotta è deliberatamente piccola e in JPEG anche quando
l'originale è PNG: non deve conservare né trasparenza né qualità, deve solo
farsi riconoscere. Chi vuole l'immagine vera la apre.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

#: Formati che Pillow apre in modo affidabile e che ha senso mostrare in
#: galleria. HEIC resta fuori: richiede un plugin esterno, e sul NAS di solito
#: esiste già la copia JPEG.
ESTENSIONI = frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".avif", ".tif", ".tiff"})

#: Lato massimo. Sopra i 320 pixel una miniatura non si legge meglio, pesa solo
#: di più: su una griglia da cento immagini la differenza si sente.
LATO = 320

#: Oltre questa dimensione il file non viene nemmeno aperto. Un'immagine
#: enorme, o un file che finge di esserlo, occuperebbe memoria per il tempo
#: della decodifica e bloccherebbe le altre richieste.
LIMITE_BYTE = 80 * 1024 * 1024


class NonUnImmagine(RuntimeError):
    """Il file non è un'immagine che sappiamo ridurre."""


def e_immagine(nome: str) -> bool:
    return Path(nome).suffix.lower() in ESTENSIONI


def _nome_cache(percorso: Path, modificato: float, dimensione: int) -> str:
    """Nome del file in cache, legato anche a data e dimensione dell'originale.

    Serve a far scadere la miniatura da sola: se la foto viene sostituita con
    un'altra dello stesso nome, cambia l'impronta e la vecchia miniatura non
    viene più trovata, invece di restare a mostrare l'immagine di prima.
    """
    impronta = hashlib.sha256(f"{percorso}|{modificato}|{dimensione}|{LATO}".encode()).hexdigest()
    return f"{impronta}.jpg"


def produci_video(originale: Path, cache: Path) -> Path:
    """La miniatura di un video: un fotogramma, con la stessa cache.

    Vive qui e non in `fotogrammi` perche' la regola della cache — nome legato
    a data e dimensione dell'originale — deve valere per tutti allo stesso
    modo, altrimenti un video sostituito continuerebbe a mostrare il vecchio
    fotogramma.
    """
    from app.services import fotogrammi

    try:
        info = originale.stat()
    except OSError as errore:
        raise NonUnImmagine("Il file non e' leggibile.") from errore

    cache.mkdir(parents=True, exist_ok=True)
    destinazione = cache / _nome_cache(originale, info.st_mtime, info.st_size)
    if destinazione.exists():
        return destinazione

    try:
        return fotogrammi.produci(originale, destinazione)
    except fotogrammi.NonUnVideo as errore:
        raise NonUnImmagine(str(errore)) from errore


def produci(originale: Path, cache: Path) -> Path:
    """Restituisce la miniatura, generandola solo se non c'è già.

    Sincrona di proposito: la chiama un thread separato, perché sia la lettura
    da NFS sia la decodifica dell'immagine possono fermarsi per secondi e non
    devono bloccare le altre richieste.
    """
    if not e_immagine(originale.name):
        raise NonUnImmagine(f"{originale.name} non e' un'immagine.")

    try:
        info = originale.stat()
    except OSError as errore:
        raise NonUnImmagine("Il file non e' leggibile.") from errore

    if info.st_size > LIMITE_BYTE:
        raise NonUnImmagine("Immagine troppo grande per una miniatura.")

    cache.mkdir(parents=True, exist_ok=True)
    destinazione = cache / _nome_cache(originale, info.st_mtime, info.st_size)
    if destinazione.exists():
        return destinazione

    try:
        with Image.open(originale) as immagine:
            # `exif_transpose` applica l'orientamento scritto dalla macchina
            # fotografica: senza, le foto scattate in verticale escono coricate,
            # ed e' il difetto piu' evidente di una galleria.
            corretta = ImageOps.exif_transpose(immagine)
            corretta = corretta.convert("RGB")
            corretta.thumbnail((LATO, LATO), Image.Resampling.LANCZOS)

            # Scrittura in un file temporaneo e rinomina: due richieste
            # simultanee sulla stessa foto non devono lasciare in cache un
            # JPEG scritto a meta'.
            parziale = destinazione.with_suffix(".parziale")
            corretta.save(parziale, "JPEG", quality=80, optimize=True)
            parziale.replace(destinazione)
    except (UnidentifiedImageError, OSError, ValueError) as errore:
        raise NonUnImmagine("Immagine non leggibile.") from errore

    return destinazione
