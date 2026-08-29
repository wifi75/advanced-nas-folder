"""Lettura dei montaggi NFS gia' presenti in /etc/fstab.

Serve a chi il pannello lo installa su una macchina che i mount ce li ha gia':
riscriverli a mano nel pannello significa ricopiare server, percorsi e opzioni
senza sbagliare, e poi accorgersi di aver dimenticato una riga.

Questo modulo **legge soltanto**. Commentare una riga di fstab e' un'azione a
parte, esplicita, con copia di sicurezza: una riga sbagliata in quel file puo'
impedire l'avvio della macchina, e non e' qualcosa che debba succedere come
effetto collaterale di un import.
"""

from __future__ import annotations

import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path

from anf_agent.protocol import CodiceErrore, ErroreAgent

logger = logging.getLogger("anf.agent.fstab")

FSTAB = Path("/etc/fstab")

#: Tipi di filesystem che interessano al pannello.
_TIPI = frozenset({"nfs", "nfs4"})

MARCATORE = "# disattivata da Advanced NAS Folder"


def _interessante(campi: list[str]) -> bool:
    return len(campi) >= 3 and campi[2] in _TIPI and ":" in campi[0]


def elenca(percorso: Path = FSTAB) -> list[dict[str, str]]:
    """I montaggi NFS descritti in fstab, uno per riga attiva.

    Le righe commentate non compaiono: sono gia' spente, e proporle come da
    importare farebbe credere che siano in uso.
    """
    try:
        contenuto = percorso.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise ErroreAgent(
            CodiceErrore.COMANDO_FALLITO, f"Impossibile leggere {percorso}: {exc.strerror}"
        ) from exc

    trovati: list[dict[str, str]] = []
    for numero, riga in enumerate(contenuto.splitlines(), start=1):
        pulita = riga.strip()
        if not pulita or pulita.startswith("#"):
            continue

        campi = pulita.split()
        if not _interessante(campi):
            continue

        server, _, export = campi[0].partition(":")
        trovati.append(
            {
                "riga": str(numero),
                "server": server,
                "export": export,
                "mountpoint": campi[1],
                "tipo": campi[2],
                "opzioni": campi[3] if len(campi) > 3 else "defaults",
            }
        )

    return trovati


def disattiva(mountpoint: str, percorso: Path = FSTAB) -> dict[str, str]:
    """Commenta la riga di fstab che monta `mountpoint`, dopo averne fatto copia.

    Non cancella nulla: la riga resta leggibile con un marcatore che dice chi
    l'ha spenta e quando. Chi si trova davanti un fstab modificato deve poter
    capire cos'e' successo senza indovinare.
    """
    try:
        contenuto = percorso.read_text(encoding="utf-8")
    except OSError as exc:
        raise ErroreAgent(
            CodiceErrore.COMANDO_FALLITO, f"Impossibile leggere {percorso}: {exc.strerror}"
        ) from exc

    righe = contenuto.splitlines(keepends=True)
    toccate = 0
    nuove: list[str] = []

    for riga in righe:
        campi = riga.strip().split()
        if not riga.strip().startswith("#") and _interessante(campi) and campi[1] == mountpoint:
            quando = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
            nuove.append(f"{MARCATORE} il {quando}\n#{riga}")
            toccate += 1
        else:
            nuove.append(riga)

    if toccate == 0:
        raise ErroreAgent(
            CodiceErrore.NON_TROVATO,
            f"Nessuna riga NFS attiva per {mountpoint} in {percorso}.",
        )

    # La copia di sicurezza prima della scrittura, sempre: se qualcosa va
    # storto, rimettere il file com'era deve essere una copia, non un lavoro
    # di ricostruzione.
    copia = percorso.with_name(f"fstab.anf-{datetime.now(UTC):%Y%m%d-%H%M%S}")
    try:
        shutil.copy2(percorso, copia)
        temporaneo = percorso.with_name(f"{percorso.name}.anf-nuovo")
        temporaneo.write_text("".join(nuove), encoding="utf-8")
        temporaneo.chmod(0o644)
        temporaneo.replace(percorso)
    except OSError as exc:
        raise ErroreAgent(
            CodiceErrore.COMANDO_FALLITO, f"Impossibile aggiornare {percorso}: {exc.strerror}"
        ) from exc

    logger.info("riga fstab per %s commentata, copia in %s", mountpoint, copia)
    return {"mountpoint": mountpoint, "copia": str(copia), "righe": str(toccate)}
