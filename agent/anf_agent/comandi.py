"""Esecuzione dei comandi di sistema.

Unico punto del progetto in cui si lancia un processo esterno. Regole:

* si passa SEMPRE una lista di argomenti, mai una stringa, e mai `shell=True`;
* ogni comando ha un timeout, altrimenti un NAS irraggiungibile blocca l'agent;
* l'ambiente e ridotto al minimo.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

from anf_agent.protocol import CodiceErrore, ErroreAgent

logger = logging.getLogger("anf.agent.comandi")

#: Ambiente minimo: nessuna variabile ereditata dal chiamante.
_AMBIENTE = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C"}


@dataclass(frozen=True, slots=True)
class Esito:
    codice: int
    stdout: str
    stderr: str

    @property
    def riuscito(self) -> bool:
        return self.codice == 0

    @property
    def messaggio_errore(self) -> str:
        """Ultima riga utile di stderr, che e quella che dice cosa e andato storto."""
        righe = [r.strip() for r in self.stderr.splitlines() if r.strip()]
        return righe[-1] if righe else f"comando terminato con codice {self.codice}"


def esegui(argomenti: list[str], *, timeout: float = 30.0) -> Esito:
    """Esegue un comando e ne restituisce l'esito, senza sollevare eccezioni."""
    if not argomenti or not all(isinstance(a, str) for a in argomenti):
        raise ErroreAgent(CodiceErrore.INTERNO, "Comando costruito in modo non valido.")

    logger.debug("esecuzione: %s", argomenti)
    try:
        completato = subprocess.run(  # noqa: S603 - argomenti validati, nessuna shell
            argomenti,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_AMBIENTE,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ErroreAgent(
            CodiceErrore.TIMEOUT,
            f"Il comando {argomenti[0]!r} non ha risposto entro {timeout:.0f} secondi.",
        ) from exc
    except FileNotFoundError as exc:
        raise ErroreAgent(
            CodiceErrore.COMANDO_FALLITO, f"Comando non disponibile: {argomenti[0]!r}"
        ) from exc

    return Esito(
        codice=completato.returncode,
        stdout=completato.stdout or "",
        stderr=completato.stderr or "",
    )


def esegui_o_fallisci(argomenti: list[str], *, timeout: float = 30.0) -> str:
    esito = esegui(argomenti, timeout=timeout)
    if not esito.riuscito:
        raise ErroreAgent(CodiceErrore.COMANDO_FALLITO, esito.messaggio_errore)
    return esito.stdout
