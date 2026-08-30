"""Miniature dei video: un fotogramma estratto con ffmpeg.

Perché non con Pillow, come per le immagini: decodificare un video richiede i
codec, e portarseli dentro Python significherebbe una dipendenza enorme per
produrre un JPEG da 9 kilobyte. `ffmpeg` è già il programma che ogni server
multimediale ha, e qui viene usato per una cosa sola.

**Il fotogramma non è il primo.** L'inizio di un video è quasi sempre nero, o
una schermata di apertura: si prende a un decimo della durata, che è dove
comincia il contenuto vero. Su un video di due secondi quel decimo sono due
decimi di secondo, ed è comunque meglio del fotogramma zero.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from app.services.miniature import LATO

logger = logging.getLogger("anf.fotogrammi")

#: Estensioni per cui vale la pena provare. L'elenco è volutamente corto: sono
#: i contenitori che un NAS domestico produce o riceve davvero.
ESTENSIONI = frozenset({".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi"})

#: Oltre questo tempo si rinuncia. Un video corrotto può far girare ffmpeg
#: all'infinito, e una miniatura non vale il blocco di un thread.
TIMEOUT = 20


class NonUnVideo(RuntimeError):
    """Il file non è un video da cui sappiamo estrarre un fotogramma."""


def e_video(nome: str) -> bool:
    return Path(nome).suffix.lower() in ESTENSIONI


def disponibile() -> bool:
    """Vero se ffmpeg è installato. Il pannello funziona anche senza: i video
    restano con l'icona del tipo, come prima."""
    try:
        subprocess.run(  # noqa: S603
            ["ffmpeg", "-version"],  # noqa: S607
            capture_output=True,
            timeout=5,
            check=True,
        )
    except OSError, subprocess.SubprocessError:
        return False
    return True


def _durata(video: Path) -> float | None:
    try:
        esito = subprocess.run(  # noqa: S603
            [  # noqa: S607
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(video),
            ],
            capture_output=True,
            timeout=TIMEOUT,
            check=True,
            text=True,
        )
        return float(json.loads(esito.stdout)["format"]["duration"])
    except OSError, subprocess.SubprocessError, KeyError, ValueError, json.JSONDecodeError:
        return None


def produci(video: Path, destinazione: Path) -> Path:
    """Estrae un fotogramma e lo salva come JPEG in `destinazione`."""
    if not e_video(video.name):
        raise NonUnVideo(f"{video.name} non e' un video.")

    durata = _durata(video)
    if durata is None or durata <= 0:
        raise NonUnVideo("Durata del video non leggibile.")

    # Un decimo della durata, ma senza uscire dal video: un file di due secondi
    # chiede due decimi di secondo, e saltare oltre la fine produce un file
    # vuoto senza che ffmpeg segnali un errore.
    istante = min(durata * 0.1, max(durata - 0.1, 0))

    destinazione.parent.mkdir(parents=True, exist_ok=True)
    parziale = destinazione.with_suffix(".parziale")
    try:
        subprocess.run(  # noqa: S603
            [  # noqa: S607
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                # Prima di `-i`: cosi' ffmpeg salta senza decodificare tutto
                # quello che precede, che su un file lungo e' la differenza fra
                # un istante e diversi secondi.
                "-ss",
                f"{istante:.3f}",
                "-i",
                str(video),
                "-frames:v",
                "1",
                "-vf",
                f"scale={LATO}:-1",
                str(parziale),
            ],
            capture_output=True,
            timeout=TIMEOUT,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as errore:
        parziale.unlink(missing_ok=True)
        raise NonUnVideo("Fotogramma non estraibile.") from errore

    if not parziale.exists() or parziale.stat().st_size == 0:
        parziale.unlink(missing_ok=True)
        raise NonUnVideo("Il video non ha prodotto nessun fotogramma.")

    parziale.replace(destinazione)
    return destinazione
