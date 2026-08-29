"""Operazioni che modificano il contenuto delle cartelle pubblicate.

A differenza di tutto il resto del progetto, qui si **scrive sul NAS**. Tre
regole valgono per ogni funzione di questo modulo:

* origine e destinazione vengono risolte con `percorsi.risolvi`, che verifica
  il percorso *dopo* aver seguito i collegamenti simbolici: un collegamento
  dentro la cartella pubblicata che punta fuori e' il modo piu semplice di
  aggirare un controllo fatto sulla stringa;
* non si sovrascrive mai per sbaglio. Se la destinazione esiste, l'operazione
  fallisce e lo dice, invece di far sparire in silenzio il file di qualcuno;
* le operazioni bloccano: una `stat` su NFS puo fermarsi per secondi se il NAS
  non risponde. Vengono percio' eseguite in un thread separato, altrimenti una
  sola richiesta lenta fermerebbe tutte le altre.
"""

from __future__ import annotations

import shutil
import unicodedata
from collections.abc import Callable
from pathlib import Path

import anyio


class OperazioneRifiutata(ValueError):
    """L'operazione non si puo' fare, e il motivo e' comprensibile all'utente."""


#: Caratteri che non possono comparire nel nome di un file creato dal pannello.
#: La barra separerebbe i percorsi, gli altri sono vietati su Windows e su SMB:
#: un NAS esposto anche in SMB genererebbe file irraggiungibili da meta' dei
#: client che lo usano.
_VIETATI_NEL_NOME = set('/\\:*?"<>|') | {chr(c) for c in range(32)}

#: Nomi che su Windows non sono file ma dispositivi. Un file cosi' chiamato su
#: una condivisione SMB e' inapribile e a volte non e' nemmeno cancellabile.
_RISERVATI = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{n}" for n in range(1, 10)}
    | {f"lpt{n}" for n in range(1, 10)}
)


def valida_nome(nome: str) -> str:
    """Controlla un nome di file o cartella scelto dall'utente.

    Non e' una barriera di sicurezza — quella e' `percorsi.risolvi` — ma serve
    a non creare sul NAS nomi che poi risultano inutilizzabili.
    """
    nome = unicodedata.normalize("NFC", nome).strip()

    if not nome or nome in (".", ".."):
        raise OperazioneRifiutata("Indica un nome.")
    if len(nome) > 255:
        raise OperazioneRifiutata("Il nome è troppo lungo.")
    if any(c in _VIETATI_NEL_NOME for c in nome):
        raise OperazioneRifiutata(
            'Il nome non può contenere / \\ : * ? " < > | né caratteri di controllo.'
        )
    if nome.startswith("."):
        # I file che iniziano con un punto sono nascosti, e il pannello non li
        # mostra: crearne uno significherebbe farlo sparire subito dopo.
        raise OperazioneRifiutata("Il nome non può iniziare con un punto.")
    if nome.endswith((" ", ".")):
        # Windows li tronca in silenzio: il file creato avrebbe un altro nome.
        raise OperazioneRifiutata("Il nome non può finire con uno spazio o un punto.")
    if nome.split(".")[0].lower() in _RISERVATI:
        raise OperazioneRifiutata(f"{nome!r} è un nome riservato dal sistema.")

    return nome


def _libero(destinazione: Path) -> None:
    if destinazione.exists():
        raise OperazioneRifiutata(f"{destinazione.name!r} esiste già in questa cartella.")


def _crea_cartella(destinazione: Path) -> None:
    _libero(destinazione)
    destinazione.mkdir(parents=False)


def _rinomina(origine: Path, destinazione: Path) -> None:
    if not origine.exists():
        raise OperazioneRifiutata("L'elemento da rinominare non esiste più.")
    _libero(destinazione)
    origine.rename(destinazione)


def _sposta(origine: Path, destinazione: Path) -> None:
    if not origine.exists():
        raise OperazioneRifiutata("L'elemento da spostare non esiste più.")
    if origine == destinazione or destinazione.is_relative_to(origine):
        # Spostare una cartella dentro se stessa creerebbe un ciclo, e a
        # seconda del filesystem la si perde.
        raise OperazioneRifiutata("Non si può spostare una cartella dentro sé stessa.")
    _libero(destinazione)
    shutil.move(str(origine), str(destinazione))


def _copia(origine: Path, destinazione: Path) -> None:
    if not origine.exists():
        raise OperazioneRifiutata("L'elemento da copiare non esiste più.")
    if destinazione.is_relative_to(origine):
        raise OperazioneRifiutata("Non si può copiare una cartella dentro sé stessa.")
    _libero(destinazione)
    if origine.is_dir():
        shutil.copytree(origine, destinazione, symlinks=True)
    else:
        shutil.copy2(origine, destinazione)


def _elimina(bersaglio: Path, *, ricorsivo: bool) -> None:
    if not bersaglio.exists():
        raise OperazioneRifiutata("L'elemento non esiste più.")

    if bersaglio.is_dir():
        # Una cartella piena si cancella solo se e stato chiesto in modo
        # esplicito: il caso in cui qualcuno crede di cancellare una cartella
        # vuota e ne perde il contenuto e troppo facile da produrre.
        if not ricorsivo and any(bersaglio.iterdir()):
            raise OperazioneRifiutata(
                "La cartella non è vuota: conferma di volerla eliminare con tutto il contenuto."
            )
        shutil.rmtree(bersaglio)
    else:
        bersaglio.unlink()


def _scrivibile(cartella: Path) -> None:
    """Verifica che si possa davvero scrivere, provandoci.

    Il pannello puo *chiedere* la scrittura, ma se la regola NFS sul NAS e in
    sola lettura il mount resta in sola lettura. Fidarsi di cio che si e
    chiesto produrrebbe un errore incomprensibile a meta' operazione.
    """
    prova = cartella / ".anf-prova-scrittura"
    try:
        prova.touch()
        prova.unlink()
    except OSError as exc:
        raise OperazioneRifiutata(
            "La cartella è in sola lettura: il NAS non consente di scrivere qui."
        ) from exc


async def _in_thread(lavoro: Callable[[], None]) -> None:
    """Esegue l'operazione fuori dal ciclo di eventi e traduce gli errori.

    Uno `OSError` grezzo dice all'utente cose come «errno 28», che non aiutano
    nessuno: qui diventa una frase che nomina il problema.
    """
    try:
        await anyio.to_thread.run_sync(lavoro)
    except OSError as exc:
        motivo = exc.strerror or str(exc)
        raise OperazioneRifiutata(f"Il sistema ha rifiutato l'operazione: {motivo}") from exc


async def crea_cartella(dentro: Path, nome: str) -> None:
    nuova = dentro / valida_nome(nome)

    def lavoro() -> None:
        _scrivibile(dentro)
        _crea_cartella(nuova)

    await _in_thread(lavoro)


async def rinomina(origine: Path, nuovo_nome: str) -> None:
    destinazione = origine.parent / valida_nome(nuovo_nome)

    def lavoro() -> None:
        _scrivibile(origine.parent)
        _rinomina(origine, destinazione)

    await _in_thread(lavoro)


async def sposta(origine: Path, cartella: Path) -> None:
    destinazione = cartella / origine.name

    def lavoro() -> None:
        _scrivibile(cartella)
        _sposta(origine, destinazione)

    await _in_thread(lavoro)


async def copia(origine: Path, cartella: Path, nome: str | None = None) -> None:
    destinazione = cartella / (valida_nome(nome) if nome else origine.name)

    def lavoro() -> None:
        _scrivibile(cartella)
        _copia(origine, destinazione)

    await _in_thread(lavoro)


async def elimina(bersaglio: Path, *, ricorsivo: bool = False) -> None:
    def lavoro() -> None:
        _scrivibile(bersaglio.parent)
        _elimina(bersaglio, ricorsivo=ricorsivo)

    await _in_thread(lavoro)
