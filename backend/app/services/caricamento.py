"""Caricamento dei file, a blocchi e riprendibile.

Un file da qualche gigabyte su una rete domestica non arriva in una richiesta
sola: basta un cambio di rete o una finestra chiusa per perdere mezz'ora di
trasferimento. Il file viene percio' inviato a blocchi, e ogni blocco viene
aggiunto in coda a un file parziale.

**Lo stato della ripresa e' il file parziale stesso**, non una riga in un
database: quanti byte sono arrivati lo dice la sua dimensione. Non c'e' nulla
da tenere allineato, nulla da ripulire se il pannello si riavvia a meta', e
un caricamento interrotto ieri riprende oggi senza che nessuno se ne sia
ricordato.

Il file parziale sta nella cartella di destinazione, non in un'area
temporanea: cosi il completamento e' una `rename` sullo stesso filesystem,
cioe' istantanea e atomica. Metterlo altrove significherebbe ricopiare
l'intero file alla fine, sulla rete, una seconda volta.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import anyio

from app.services.operazioni import OperazioneRifiutata, valida_nome

#: Prefisso e suffisso del file parziale. Il punto iniziale lo rende nascosto,
#: e il pannello non elenca i file nascosti: un caricamento a meta' non
#: compare fra i file veri.
_PREFISSO = "."
_SUFFISSO = ".anf-parziale"

#: Oltre questa dimensione un singolo blocco viene rifiutato. Non e' un limite
#: alla dimensione del file — quello lo si supera con piu' blocchi — ma al
#: quanto l'applicazione tiene in memoria per una singola richiesta.
BLOCCO_MASSIMO = 16 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class Stato:
    """Quanto e' gia' arrivato di un caricamento."""

    nome: str
    ricevuti: int
    #: Vero se il file definitivo esiste gia': caricarlo lo sovrascriverebbe.
    gia_presente: bool


def parziale(cartella: Path, nome: str) -> Path:
    """Percorso del file parziale corrispondente a un nome di destinazione."""
    return cartella / f"{_PREFISSO}{valida_nome(nome)}{_SUFFISSO}"


async def stato(cartella: Path, nome: str) -> Stato:
    """Dice da dove riprendere.

    Chiamata prima di iniziare: se restituisce `ricevuti` maggiore di zero, il
    client riparte da li' invece che dall'inizio.
    """
    definitivo = cartella / valida_nome(nome)
    in_corso = parziale(cartella, nome)

    def leggi() -> Stato:
        return Stato(
            nome=valida_nome(nome),
            ricevuti=in_corso.stat().st_size if in_corso.exists() else 0,
            gia_presente=definitivo.exists(),
        )

    try:
        return await anyio.to_thread.run_sync(leggi)
    except OSError as exc:
        raise OperazioneRifiutata(f"Cartella non leggibile: {exc.strerror}") from exc


async def aggiungi(cartella: Path, nome: str, blocco: bytes, offset: int) -> int:
    """Aggiunge un blocco in coda al file parziale e restituisce il totale.

    `offset` deve combaciare con quanto e' gia' stato ricevuto. Non e' una
    formalita': se il client si sbagliasse di posizione, scrivere comunque
    produrrebbe un file corrotto che nessuno noterebbe finche' non prova ad
    aprirlo.
    """
    if len(blocco) > BLOCCO_MASSIMO:
        raise OperazioneRifiutata("Il blocco inviato è troppo grande.")

    in_corso = parziale(cartella, nome)

    def scrivi() -> int:
        gia = in_corso.stat().st_size if in_corso.exists() else 0
        if offset != gia:
            raise OperazioneRifiutata(f"Il caricamento riparte dal byte {gia}, non da {offset}.")
        with in_corso.open("ab") as f:
            f.write(blocco)
        return gia + len(blocco)

    try:
        return await anyio.to_thread.run_sync(scrivi)
    except OSError as exc:
        motivo = exc.strerror or str(exc)
        raise OperazioneRifiutata(f"Il sistema ha rifiutato la scrittura: {motivo}") from exc


async def completa(cartella: Path, nome: str, dimensione_attesa: int | None = None) -> Path:
    """Trasforma il file parziale nel file definitivo.

    La `rename` finale e' atomica: non esiste un istante in cui il file
    esiste ma e' incompleto, e chi lo scarica non puo' trovarne meta'.
    """
    definitivo = cartella / valida_nome(nome)
    in_corso = parziale(cartella, nome)

    def concludi() -> Path:
        if not in_corso.exists():
            raise OperazioneRifiutata("Non risulta nessun caricamento da completare.")

        arrivati = in_corso.stat().st_size
        if dimensione_attesa is not None and arrivati != dimensione_attesa:
            # Non si completa un file di cui manca un pezzo: meglio poterlo
            # riprendere che ritrovarselo troncato fra i file buoni.
            raise OperazioneRifiutata(
                f"Il caricamento è incompleto: {arrivati} byte su {dimensione_attesa}."
            )
        if definitivo.exists():
            raise OperazioneRifiutata(f"{definitivo.name!r} esiste già in questa cartella.")

        in_corso.rename(definitivo)
        return definitivo

    try:
        return await anyio.to_thread.run_sync(concludi)
    except OSError as exc:
        motivo = exc.strerror or str(exc)
        raise OperazioneRifiutata(f"Il sistema ha rifiutato l'operazione: {motivo}") from exc


async def annulla(cartella: Path, nome: str) -> None:
    """Butta via un caricamento a meta'.

    Serve perche' un file parziale abbandonato resterebbe li' a occupare
    spazio sul NAS senza che nessuno sappia piu' cos'era.
    """
    in_corso = parziale(cartella, nome)
    try:
        await anyio.to_thread.run_sync(lambda: in_corso.unlink(missing_ok=True))
    except OSError as exc:
        motivo = exc.strerror or str(exc)
        raise OperazioneRifiutata(f"Non riesco a eliminare il file parziale: {motivo}") from exc
