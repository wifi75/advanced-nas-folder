"""Scoperta delle condivisioni NFS e stato reale dei montaggi."""

from __future__ import annotations

import json
import logging
from pathlib import PurePosixPath

from anf_agent.comandi import esegui
from anf_agent.protocol import CodiceErrore, ErroreAgent

logger = logging.getLogger("anf.agent.nfs")


def elenca_esportazioni(server: str) -> list[dict[str, str]]:
    """Condivisioni esportate dal NAS, con i client autorizzati.

    E cio che permette al pannello di mostrare un elenco da cui scegliere,
    invece di far digitare a mano un percorso che deve indovinare.
    """
    esito = esegui(["showmount", "--exports", "--no-headers", server], timeout=15)
    if not esito.riuscito:
        raise ErroreAgent(
            CodiceErrore.COMANDO_FALLITO,
            f"Impossibile interrogare {server}: {esito.messaggio_errore}. "
            "Verifica che il NAS sia raggiungibile e che NFS sia attivo.",
        )

    esportazioni: list[dict[str, str]] = []
    for riga in esito.stdout.splitlines():
        riga = riga.strip()
        if not riga or riga.startswith("Export list"):
            continue
        percorso, _, client = riga.partition(" ")
        if percorso.startswith("/"):
            esportazioni.append({"percorso": percorso, "client": client.strip() or "*"})

    return sorted(esportazioni, key=lambda e: e["percorso"])


def versioni_supportate(server: str) -> list[str]:
    """Versioni del protocollo NFS che il NAS espone davvero.

    Serve a spiegare l'errore piu frequente: una configurazione che chiede
    NFSv4 a un NAS che espone solo la v3 fallisce con 'Protocol not supported',
    un messaggio che da solo non dice cosa fare.
    """
    esito = esegui(["rpcinfo", "-p", server], timeout=15)
    if not esito.riuscito:
        return []

    versioni: set[str] = set()
    for riga in esito.stdout.splitlines():
        pezzi = riga.split()
        if len(pezzi) >= 5 and pezzi[-1] == "nfs":
            versioni.add(pezzi[1])
    return sorted(versioni, key=int)


def stato_montaggio(mountpoint: PurePosixPath) -> dict[str, object]:
    """Stato REALE del montaggio, letto dal sistema e non dedotto.

    La distinzione fra cio che si e chiesto e cio che si e ottenuto e il punto
    centrale: il pannello puo chiedere la scrittura, ma se la regola NFS sul NAS
    e in sola lettura il mount resta in sola lettura. Mostrare l'intenzione al
    posto della realta significherebbe mentire all'utente.
    """
    # Niente filtro sul tipo: con l'automount il percorso risulta prima di tipo
    # autofs, e filtrando su nfs si vedrebbe "non montato" anche a montaggio
    # avvenuto. Il tipo effettivo viene letto e riportato.
    esito = esegui(
        [
            "findmnt",
            "--json",
            "--output",
            "TARGET,SOURCE,FSTYPE,OPTIONS",
            str(mountpoint),
        ],
        timeout=15,
    )

    if not esito.riuscito or not esito.stdout.strip():
        return {"montato": False, "opzioni": None, "sorgente": None, "scrittura": None}

    try:
        voci = json.loads(esito.stdout)["filesystems"]
    except json.JSONDecodeError, KeyError:
        logger.warning("Uscita di findmnt non interpretabile per %s", mountpoint)
        return {"montato": False, "opzioni": None, "sorgente": None, "scrittura": None}

    # Se il percorso e sotto automount compaiono due voci: quella autofs e,
    # a montaggio avvenuto, quella NFS. Vale la seconda.
    voce = next((v for v in voci if str(v.get("fstype", "")).startswith("nfs")), None)
    if voce is None:
        return {
            "montato": False,
            "opzioni": None,
            "sorgente": None,
            "scrittura": None,
            "automount_pronto": any(v.get("fstype") == "autofs" for v in voci),
        }

    opzioni = str(voce.get("options", ""))
    elenco = opzioni.split(",")

    return {
        "montato": True,
        "sorgente": voce.get("source"),
        "tipo": voce.get("fstype"),
        "opzioni": opzioni,
        # "rw" e "ro" compaiono sempre fra le opzioni effettive.
        "scrittura": "rw" in elenco and "ro" not in elenco,
    }


def prova_scrittura(mountpoint: PurePosixPath) -> bool | None:
    """Verifica sul campo se il mount e davvero scrivibile.

    Le opzioni riportate da findmnt dicono cosa ha chiesto il client, ma il NAS
    puo negare la scrittura per conto suo: l'unica prova certa e provare.
    Restituisce None se il mount non e accessibile.
    """
    prova = PurePosixPath(mountpoint) / ".anf-prova-scrittura"
    esito = esegui(["touch", str(prova)], timeout=10)
    if esito.riuscito:
        esegui(["rm", "-f", str(prova)], timeout=10)
        return True
    if "read-only" in esito.stderr.lower() or "sola lettura" in esito.stderr.lower():
        return False
    return None
