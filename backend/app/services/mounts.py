"""Logica dei mount: traduce fra il modello del database e l'agent."""

from __future__ import annotations

from typing import Any

from app.models import Mount
from app.models.enums import AccessoNFS, StatoMount
from app.services import agent_client

#: Opzioni applicate a ogni mount, scelte e validate sul campo.
#:
#: - nofail e automount: il server si avvia anche a NAS spento, e monta alla
#:   prima richiesta invece di restare giu fino al riavvio successivo
#: - soft con timeout brevi: a NAS irraggiungibile il web server riceve un
#:   errore invece di restare appeso con i worker bloccati
#: - nolock: mount senza necessita di lock, nessuna dipendenza da rpc-statd
OPZIONI_BASE = [
    "noatime",
    "soft",
    "nolock",
    "_netdev",
    "nofail",
    "proto=tcp",
    "timeo=150",
    "retrans=3",
    "x-systemd.mount-timeout=30",
]


def opzioni_per(mount: Mount) -> list[str]:
    """Costruisce le opzioni di mount a partire dal record."""
    opzioni = [str(mount.requested_access), *OPZIONI_BASE]
    if mount.automount:
        opzioni.append("x-systemd.automount")
        opzioni.append(f"x-systemd.idle-timeout={mount.idle_timeout}")
    return opzioni


def dati_creazione(mount: Mount) -> dict[str, Any]:
    return {
        "slug": mount.slug,
        "server": mount.server,
        "export_path": mount.export_path,
        "nfs_version": mount.nfs_version,
        "automount": mount.automount,
        "idle_timeout": mount.idle_timeout,
        "opzioni": opzioni_per(mount),
    }


def applica_stato(mount: Mount, stato: dict[str, Any]) -> None:
    """Riporta nel record cio che il sistema ha detto davvero.

    Lo stato richiesto resta quello che e: qui si aggiorna solo il rilevato.
    Tenerli separati e cio che permette al pannello di dire "hai chiesto la
    scrittura ma il NAS la nega" invece di mostrare un'informazione falsa.
    """
    montato = bool(stato.get("montato"))
    mount.state = StatoMount.MONTATO if montato else StatoMount.SMONTATO
    mount.effective_options = stato.get("opzioni")

    # La prova sul campo vince sulle opzioni dichiarate: il NAS puo negare la
    # scrittura anche a un mount richiesto in lettura-scrittura.
    verificata = stato.get("scrittura_verificata")
    mount.effective_read_write = (
        bool(verificata) if verificata is not None else stato.get("scrittura")
    )
    if montato:
        mount.last_error = None


def avviso_per(mount: Mount) -> str | None:
    """Messaggio da mostrare in evidenza quando richiesto ed effettivo divergono."""
    if (
        mount.requested_access is AccessoNFS.LETTURA_SCRITTURA
        and mount.effective_read_write is False
    ):
        return (
            "È stata richiesta la scrittura, ma il NAS la sta negando: la "
            "condivisione risulta in sola lettura. Va abilitata anche lato NAS, "
            "nei permessi NFS della cartella condivisa."
        )
    if mount.state is StatoMount.ERRORE and mount.last_error:
        return mount.last_error
    return None


async def leggi_stato(mount: Mount) -> dict[str, Any] | None:
    """Interroga l'agent per lo stato reale. None se l'agent non risponde."""
    try:
        return await agent_client.chiedi("mount.status", {"slug": mount.slug})
    except agent_client.AgentNonDisponibile, agent_client.AgentRifiuta:
        return None
