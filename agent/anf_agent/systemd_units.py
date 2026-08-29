"""Generazione e gestione delle unit systemd di montaggio.

Si generano unit, non righe in `/etc/fstab`. Motivo: fstab e un file unico
condiviso da tutto il sistema, e una riga sbagliata scritta da un pannello web
puo impedire l'avvio del server. Una unit e un file per mount: si aggiunge e si
rimuove da sola, e una unit non valida resta un problema isolato.
"""

from __future__ import annotations

import logging
from pathlib import Path, PurePosixPath

from anf_agent.comandi import esegui, esegui_o_fallisci
from anf_agent.protocol import CodiceErrore, ErroreAgent

logger = logging.getLogger("anf.agent.systemd")

CARTELLA_UNIT = Path("/etc/systemd/system")

#: Marcatore scritto in ogni unit generata. L'agent non tocca MAI una unit che
#: non riporti questa riga: cosi non puo danneggiare configurazioni altrui.
MARCATORE = "# Generato da Advanced NAS Folder - non modificare a mano"

_MOUNT = """{marcatore}
[Unit]
Description=ANF - {slug}
After=network-online.target
Wants=network-online.target

[Mount]
What={server}:{export}
Where={mountpoint}
Type=nfs
Options={opzioni}
TimeoutSec=30

[Install]
WantedBy=multi-user.target
"""

_AUTOMOUNT = """{marcatore}
[Unit]
Description=ANF - montaggio su richiesta di {slug}

[Automount]
Where={mountpoint}
TimeoutIdleSec={idle}

[Install]
WantedBy=multi-user.target
"""


def nome_unit(mountpoint: PurePosixPath, suffisso: str) -> str:
    """Nome della unit corrispondente a un percorso.

    Delegato a `systemd-escape`, che conosce le regole esatte: reimplementarle
    a mano e un classico modo di sbagliare sui casi limite.
    """
    uscita = esegui_o_fallisci(
        ["systemd-escape", "--path", f"--suffix={suffisso}", str(mountpoint)], timeout=5
    )
    nome = uscita.strip()
    if not nome or "/" in nome:
        raise ErroreAgent(CodiceErrore.INTERNO, f"Nome di unit non valido: {nome!r}")
    return nome


def _e_nostra(percorso: Path) -> bool:
    try:
        return MARCATORE in percorso.read_text(encoding="utf-8")
    except OSError:
        return False


def _scrivi(percorso: Path, contenuto: str) -> None:
    if percorso.exists() and not _e_nostra(percorso):
        raise ErroreAgent(
            CodiceErrore.VALIDAZIONE,
            f"{percorso.name} esiste ma non e stata generata da questo pannello: "
            "non viene sovrascritta.",
        )
    # Scrittura atomica: un'interruzione a meta lascerebbe una unit troncata,
    # che systemd rifiuterebbe di caricare.
    temporaneo = percorso.with_suffix(percorso.suffix + ".nuovo")
    temporaneo.write_text(contenuto, encoding="utf-8")
    temporaneo.chmod(0o644)
    temporaneo.replace(percorso)


def scrivi_unit(
    *,
    slug: str,
    server: str,
    export: str,
    mountpoint: PurePosixPath,
    opzioni: list[str],
    automount: bool,
    idle_timeout: int,
) -> dict[str, str]:
    """Genera la unit di mount e, se richiesto, quella di montaggio su richiesta."""
    Path(mountpoint).mkdir(parents=True, exist_ok=True)

    nome_mount = nome_unit(mountpoint, "mount")
    _scrivi(
        CARTELLA_UNIT / nome_mount,
        _MOUNT.format(
            marcatore=MARCATORE,
            slug=slug,
            server=server,
            export=export,
            mountpoint=mountpoint,
            opzioni=",".join(opzioni),
        ),
    )

    generate = {"mount": nome_mount}

    if automount:
        nome_auto = nome_unit(mountpoint, "automount")
        _scrivi(
            CARTELLA_UNIT / nome_auto,
            _AUTOMOUNT.format(
                marcatore=MARCATORE, slug=slug, mountpoint=mountpoint, idle=idle_timeout
            ),
        )
        generate["automount"] = nome_auto

    ricarica()
    return generate


def rimuovi_unit(mountpoint: PurePosixPath) -> list[str]:
    """Ferma e cancella le unit di un mount. Rimuove solo quelle nostre."""
    rimosse: list[str] = []
    for suffisso in ("automount", "mount"):
        nome = nome_unit(mountpoint, suffisso)
        percorso = CARTELLA_UNIT / nome
        if not percorso.exists():
            continue
        if not _e_nostra(percorso):
            logger.warning("%s non e stata generata da noi: lasciata dov'e", nome)
            continue
        esegui(["systemctl", "disable", "--now", nome], timeout=45)
        percorso.unlink(missing_ok=True)
        rimosse.append(nome)

    if rimosse:
        ricarica()
        esegui(["systemctl", "reset-failed"], timeout=15)
    return rimosse


def ricarica() -> None:
    esegui_o_fallisci(["systemctl", "daemon-reload"], timeout=30)


def avvia(nome: str) -> None:
    esegui_o_fallisci(["systemctl", "enable", "--now", nome], timeout=60)


def ferma(nome: str) -> None:
    esegui(["systemctl", "disable", "--now", nome], timeout=45)
