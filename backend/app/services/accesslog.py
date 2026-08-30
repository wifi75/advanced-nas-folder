"""Lettura dell'access log del web server.

È l'unico modo per sapere quanti byte sono davvero arrivati: la consegna dei
file è delegata al web server, e quando questo comincia a inviarli
l'applicazione è già uscita di scena. Il numero lo scrive lui, a
trasferimento concluso, nel suo log.

Il lettore segue il file come farebbe `tail -f`, e regge la rotazione: quando
il file viene sostituito, l'inode cambia e si riparte dall'inizio di quello
nuovo. Senza, dopo la prima rotazione notturna il monitoraggio smetterebbe di
aggiornarsi in silenzio.
"""

from __future__ import annotations

import contextlib
import logging
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

import anyio

from app.models.enums import StatoTrasferimento

logger = logging.getLogger("anf.accesslog")

#: Due formati, non uno.
#:
#: Il combinato — quello predefinito di Apache e Nginx — mette due campi fra
#: l'indirizzo e la data: `ip - - [data]`. Il formato che l'installer
#: configura, invece, va dall'indirizzo direttamente alla data, perche' quei
#: due campi sono sempre vuoti e occupano spazio nel log per niente.
#:
#: Riconoscerne uno solo significa non contare mai nulla: e' esattamente cosa
#: succedeva, e ogni trasferimento restava «in corso» per sempre.
_RIGA = re.compile(
    r'^(?P<ip>\S+) (?:\S+ \S+ )?\[[^\]]+\] "(?P<metodo>[A-Z]+) (?P<url>\S+) [^"]*" '
    r"(?P<stato>\d{3}) (?P<byte>\d+|-)"
)

#: Quanto si aspetta prima di rileggere, quando il file non è cresciuto.
ATTESA = 1.0


@dataclass(frozen=True, slots=True)
class Riga:
    ip: str
    percorso: str
    stato: int
    byte: int

    @property
    def esito(self) -> StatoTrasferimento:
        # 200 e 206 sono entrambi trasferimenti riusciti: il secondo è la
        # ripresa di uno interrotto, e contarla come fallimento farebbe
        # sembrare rotto un sistema che sta funzionando come deve.
        if self.stato in (200, 206):
            return StatoTrasferimento.COMPLETATO
        if self.stato in (499, 408):
            return StatoTrasferimento.INTERROTTO
        return StatoTrasferimento.FALLITO


def analizza(riga: str) -> Riga | None:
    """Estrae da una riga di log ciò che serve, o `None` se non è pertinente."""
    trovato = _RIGA.match(riga)
    if trovato is None:
        return None

    dati = trovato.groupdict()
    if dati["metodo"] not in ("GET", "HEAD"):
        return None

    # Interessano solo le consegne di file: il resto del traffico verso il
    # pannello non è un trasferimento.
    percorso = urlsplit(dati["url"]).path
    if "/archivio/" not in percorso and "/link/" not in percorso:
        return None
    if not percorso.endswith("/file"):
        return None

    query = urlsplit(dati["url"]).query
    richiesto = ""
    for pezzo in query.split("&"):
        chiave, _, valore = pezzo.partition("=")
        if chiave == "percorso":
            richiesto = unquote(valore.replace("+", " "))
            break

    return Riga(
        ip=dati["ip"],
        percorso=richiesto,
        stato=int(dati["stato"]),
        byte=0 if dati["byte"] == "-" else int(dati["byte"]),
    )


async def segui(percorso: Path) -> AsyncIterator[Riga]:
    """Righe pertinenti dell'access log, man mano che vengono scritte.

    Parte dalla fine: all'avvio non interessa ricostruire la storia, ma
    seguire quello che succede da adesso.
    """
    posizione: int | None = None
    inode: int | None = None

    while True:
        try:
            stato = await anyio.to_thread.run_sync(percorso.stat)
        except OSError:
            # Il file può non esistere ancora, o essere stato appena ruotato.
            await anyio.sleep(ATTESA)
            continue

        if inode != stato.st_ino:
            # File nuovo: o è il primo giro, o c'è stata una rotazione.
            inode = stato.st_ino
            posizione = stato.st_size if posizione is None else 0

        if stato.st_size < (posizione or 0):
            # Il file si è accorciato senza cambiare inode: troncato sul posto.
            posizione = 0

        if stato.st_size == posizione:
            await anyio.sleep(ATTESA)
            continue

        def leggi(da: int) -> tuple[str, int]:
            with percorso.open("r", encoding="utf-8", errors="replace") as f:
                f.seek(da)
                testo = f.read()
                return testo, f.tell()

        blocco, posizione = await anyio.to_thread.run_sync(leggi, posizione or 0)
        for riga in blocco.splitlines():
            analizzata = analizza(riga)
            if analizzata is not None:
                yield analizzata


async def sorveglia(percorso: Path) -> None:
    """Aggiorna i trasferimenti con i byte letti dal log. Gira in sottofondo."""
    from app.core.database import SessionLocal
    from app.services import trasferimenti

    logger.info("lettura dell'access log da %s", percorso)
    async for riga in segui(percorso):
        with contextlib.suppress(Exception):
            # Un errore qui non deve fermare la sorveglianza: il monitoraggio
            # è un di più, e non vale interromperlo per una riga storta.
            async with SessionLocal() as sessione:
                await trasferimenti.concludi(
                    sessione,
                    riga.percorso,
                    client_ip=riga.ip,
                    byte=riga.byte,
                    stato=riga.esito,
                )
