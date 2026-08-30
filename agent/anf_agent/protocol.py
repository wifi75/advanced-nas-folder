"""Protocollo fra l'API e l'agent privilegiato.

Insieme CHIUSO di verbi. Non esiste un verbo generico, non esiste un "esegui
questo": ogni operazione che l'agent sa fare e elencata qui, e tutto il resto
viene rifiutato prima di essere interpretato.

I messaggi sono JSON delimitati da una riga: una richiesta per riga, una
risposta per riga.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Verbo(StrEnum):
    """Le uniche operazioni che l'agent accetta."""

    PING = "ping"
    NFS_DISCOVER = "nfs.discover"
    MOUNT_CREATE = "mount.create"
    MOUNT_START = "mount.start"
    MOUNT_STOP = "mount.stop"
    MOUNT_REMOVE = "mount.remove"
    MOUNT_STATUS = "mount.status"
    MOUNT_LIST = "mount.list"
    WEBSERVER_DETECT = "webserver.detect"
    VHOST_PREVIEW = "vhost.preview"
    VHOST_WRITE = "vhost.write"
    VHOST_REMOVE = "vhost.remove"
    VHOST_LIST = "vhost.list"
    SCORCIATOIE_WRITE = "scorciatoie.write"
    FSTAB_LIST = "fstab.list"
    FSTAB_DISABLE = "fstab.disable"


class CodiceErrore(StrEnum):
    """Categorie di errore, per permettere all'API di reagire in modo diverso."""

    VERBO_SCONOSCIUTO = "verbo_sconosciuto"
    RICHIESTA_MALFORMATA = "richiesta_malformata"
    VALIDAZIONE = "validazione"
    NON_TROVATO = "non_trovato"
    COMANDO_FALLITO = "comando_fallito"
    TIMEOUT = "timeout"
    INTERNO = "interno"


class ErroreAgent(Exception):
    """Errore previsto, da riportare all'API senza far cadere la connessione."""

    def __init__(self, codice: CodiceErrore, messaggio: str) -> None:
        super().__init__(messaggio)
        self.codice = codice
        self.messaggio = messaggio


@dataclass(frozen=True, slots=True)
class Richiesta:
    verbo: Verbo
    dati: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def da_json(riga: bytes) -> Richiesta:
        try:
            grezzo = json.loads(riga)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ErroreAgent(CodiceErrore.RICHIESTA_MALFORMATA, f"JSON non valido: {exc}") from exc

        if not isinstance(grezzo, dict):
            raise ErroreAgent(
                CodiceErrore.RICHIESTA_MALFORMATA, "La richiesta deve essere un oggetto."
            )

        verbo_grezzo = grezzo.get("verbo")
        try:
            verbo = Verbo(verbo_grezzo)
        except ValueError:
            raise ErroreAgent(
                CodiceErrore.VERBO_SCONOSCIUTO, f"Verbo non riconosciuto: {verbo_grezzo!r}"
            ) from None

        dati = grezzo.get("dati", {})
        if not isinstance(dati, dict):
            raise ErroreAgent(
                CodiceErrore.RICHIESTA_MALFORMATA, "Il campo 'dati' deve essere un oggetto."
            )

        return Richiesta(verbo=verbo, dati=dati)


@dataclass(frozen=True, slots=True)
class Risposta:
    ok: bool
    risultato: dict[str, Any] | None = None
    codice: CodiceErrore | None = None
    errore: str | None = None

    @staticmethod
    def successo(risultato: dict[str, Any] | None = None) -> Risposta:
        return Risposta(ok=True, risultato=risultato or {})

    @staticmethod
    def fallimento(codice: CodiceErrore, messaggio: str) -> Risposta:
        return Risposta(ok=False, codice=codice, errore=messaggio)

    def a_json(self) -> bytes:
        corpo: dict[str, Any] = {"ok": self.ok}
        if self.ok:
            corpo["risultato"] = self.risultato or {}
        else:
            corpo["codice"] = str(self.codice) if self.codice else None
            corpo["errore"] = self.errore
        return json.dumps(corpo, ensure_ascii=False).encode() + b"\n"
