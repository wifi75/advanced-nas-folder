"""Consegna dei file al client.

L'applicazione **non invia mai il contenuto**: autorizza, poi dice al web
server quale file servire e si toglie di mezzo. Motivi, in ordine di
importanza:

* il *resume* delle richieste interrotte funziona in modo nativo. `Range`,
  `If-Range`, `ETag` e le risposte `206` sono già implementate nel web server,
  e riscriverle in Python significherebbe riscriverle peggio;
* un file da un gigabyte non tiene occupato un worker per tutta la durata del
  trasferimento.

In sviluppo esiste una terza modalità che invia davvero il file da Python: è
lenta e senza resume, ma permette di lavorare senza un web server davanti.
"""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from app.core.config import get_settings

#: Tipi che il browser non deve interpretare ma scaricare. Servire HTML o SVG
#: caricati da altri con il loro tipo reale significa eseguirli nel contesto
#: del pannello: è cross-site scripting con un altro nome.
_TIPI_PERICOLOSI = frozenset(
    {
        "text/html",
        "application/xhtml+xml",
        "image/svg+xml",
        "application/xml",
        "text/xml",
    }
)


@dataclass(frozen=True, slots=True)
class Consegna:
    """Come il web server deve servire il file."""

    #: Intestazioni da mettere nella risposta vuota.
    intestazioni: dict[str, str]
    #: Percorso reale, valorizzato solo quando il file lo invia l'applicazione.
    invia_direttamente: Path | None = None
    tipo: str = "application/octet-stream"


def tipo_contenuto(nome: str) -> str:
    """Tipo MIME del file, con quelli eseguibili nel browser neutralizzati."""
    indovinato, _ = mimetypes.guess_type(nome)
    if indovinato is None or indovinato in _TIPI_PERICOLOSI:
        return "application/octet-stream"
    return indovinato


def _disposizione(nome: str, allegato: bool) -> str:
    """Intestazione `Content-Disposition` con il nome del file.

    Il nome è codificato due volte, in ASCII e in UTF-8: i client vecchi
    leggono il primo, gli altri il secondo. Senza, un file con accenti o
    cirillico arriva con un nome storpiato.
    """
    tipo = "attachment" if allegato else "inline"
    ripiego = nome.encode("ascii", "replace").decode("ascii").replace('"', "_")
    return f"{tipo}; filename=\"{ripiego}\"; filename*=UTF-8''{quote(nome)}"


def prepara(reale: Path, nome: str, *, allegato: bool = True) -> Consegna:
    """Costruisce la consegna secondo il modo configurato.

    `reale` deve essere già stato verificato: qui si assume che il percorso sia
    dentro la cartella pubblicata e che l'accesso sia consentito.
    """
    settings = get_settings()
    tipo = tipo_contenuto(nome)
    intestazioni = {
        "Content-Disposition": _disposizione(nome, allegato),
        "Content-Type": tipo,
        # Un file servito dal pannello non deve poter essere incorniciato né
        # interpretato con un tipo diverso da quello dichiarato.
        "X-Content-Type-Options": "nosniff",
    }

    match settings.download_backend:
        case "xsendfile":
            intestazioni["X-Sendfile"] = str(reale)
            return Consegna(intestazioni=intestazioni, tipo=tipo)

        case "xaccel":
            # Nginx risolve il prefisso interno sulla radice dei mount: il
            # percorso va quindi espresso relativo a quella, non assoluto.
            relativo = reale.relative_to(settings.mount_root)
            prefisso = settings.xaccel_prefix.rstrip("/")
            interno = f"{prefisso}/{PurePosixPath(*relativo.parts)}"
            intestazioni["X-Accel-Redirect"] = quote(interno)
            return Consegna(intestazioni=intestazioni, tipo=tipo)

        case _:
            # Solo per lo sviluppo: nessun resume, e il worker resta occupato.
            return Consegna(intestazioni=intestazioni, invia_direttamente=reale, tipo=tipo)
