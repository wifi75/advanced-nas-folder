"""Gestione delle condivisioni NFS dal pannello."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import Amministratore, Sessione
from app.api.errori import errore_agent
from app.core.config import get_settings
from app.models import Mount
from app.models.enums import AccessoNFS, StatoMount
from app.schemas.mount import (
    CartellaMount,
    DisattivaFstab,
    MontaggioPreesistente,
    MountCreate,
    MountDettaglio,
    MountOut,
    MountUpdate,
    ScopertaRichiesta,
    ScopertaRisposta,
    StatoEffettivo,
)
from app.services import agent_client, archivio
from app.services import mounts as servizio
from app.services.percorsi import PercorsoNonValido, normalizza_relativo, risolvi

router = APIRouter(prefix="/mounts", tags=["mount"])


async def _carica(sessione: Sessione, mount_id: int) -> Mount:
    mount = await sessione.get(Mount, mount_id)
    if mount is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Condivisione non trovata.")
    return mount


async def _dettaglio(mount: Mount) -> MountDettaglio:
    dettaglio = MountDettaglio.model_validate(mount)
    stato = await servizio.leggi_stato(mount)
    if stato is not None:
        dettaglio.effettivo = StatoEffettivo.model_validate(stato)
    dettaglio.avviso = servizio.avviso_per(mount)
    return dettaglio


@router.post("/discover", response_model=ScopertaRisposta)
async def scopri(dati: ScopertaRichiesta, _: Amministratore) -> ScopertaRisposta:
    """Elenca le condivisioni esportate da un NAS.

    È ciò che permette di scegliere da un elenco invece di digitare a mano un
    percorso che si deve indovinare.
    """
    try:
        risultato = await agent_client.chiedi("nfs.discover", {"server": dati.server})
    except (agent_client.AgentNonDisponibile, agent_client.AgentRifiuta) as exc:
        raise errore_agent(exc) from exc
    return ScopertaRisposta.model_validate(risultato)


@router.get("", response_model=list[MountOut])
async def elenca(sessione: Sessione, _: Amministratore) -> list[Mount]:
    risultato = await sessione.execute(select(Mount).order_by(Mount.label))
    return list(risultato.scalars().all())


@router.post("", response_model=MountDettaglio, status_code=status.HTTP_201_CREATED)
async def crea(dati: MountCreate, sessione: Sessione, _: Amministratore) -> MountDettaglio:
    esistente = await sessione.execute(select(Mount).where(Mount.slug == dati.slug))
    if esistente.scalar_one_or_none() is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Esiste già una condivisione con identificatore {dati.slug!r}.",
        )

    mount = Mount(
        slug=dati.slug,
        label=dati.label,
        server=dati.server,
        export_path=dati.export_path,
        # Il percorso non viene mai scelto dall'utente: lo impone l'agent a
        # partire dallo slug, dentro la radice consentita.
        mountpoint=str(get_settings().mount_root / dati.slug),
        nfs_version=dati.nfs_version,
        automount=dati.automount,
        idle_timeout=dati.idle_timeout,
        requested_access=(
            AccessoNFS.LETTURA_SCRITTURA if dati.consenti_scrittura else AccessoNFS.SOLA_LETTURA
        ),
        state=StatoMount.CONFIGURATO,
    )

    try:
        risultato = await agent_client.chiedi("mount.create", servizio.dati_creazione(mount))
    except (agent_client.AgentNonDisponibile, agent_client.AgentRifiuta) as exc:
        raise errore_agent(exc) from exc

    mount.mountpoint = str(risultato.get("mountpoint") or mount.mountpoint)
    sessione.add(mount)
    await sessione.commit()
    await sessione.refresh(mount)
    return await _dettaglio(mount)


# --- montaggi preesistenti --------------------------------------------------


def _slug_da(mountpoint: str) -> str:
    """Identificatore proposto a partire dal punto di montaggio.

    Solo una proposta: chi importa può cambiarlo. Serve a non far inventare un
    nome da zero per ogni riga di fstab.
    """
    grezzo = mountpoint.strip("/").replace("/", "-").lower()
    pulito = re.sub(r"[^a-z0-9-]+", "-", grezzo).strip("-")
    return (pulito or "importato")[:63]


@router.get("/preesistenti", response_model=list[MontaggioPreesistente])
async def preesistenti(sessione: Sessione, _: Amministratore) -> list[MontaggioPreesistente]:
    """I montaggi NFS descritti in `/etc/fstab` e non ancora gestiti dal pannello.

    Serve a chi installa il pannello su una macchina che i mount ce li ha già:
    ricopiarli a mano significa riscrivere server, percorsi e opzioni senza
    sbagliare, e poi accorgersi di aver dimenticato una riga.
    """
    try:
        risposta = await agent_client.chiedi("fstab.list", {})
    except (agent_client.AgentNonDisponibile, agent_client.AgentRifiuta) as exc:
        raise errore_agent(exc) from exc

    esistenti = await sessione.execute(select(Mount))
    gia = {(m.server, m.export_path.rstrip("/")) for m in esistenti.scalars().all()}

    trovati: list[MontaggioPreesistente] = []
    for voce in risposta.get("montaggi", []):
        trovati.append(
            MontaggioPreesistente(
                riga=int(voce["riga"]),
                server=voce["server"],
                export=voce["export"],
                mountpoint=voce["mountpoint"],
                tipo=voce["tipo"],
                opzioni=voce["opzioni"],
                slug_proposto=_slug_da(voce["mountpoint"]),
                gia_gestito=(voce["server"], voce["export"].rstrip("/")) in gia,
            )
        )
    return trovati


@router.post("/fstab/disattiva")
async def disattiva_fstab(dati: DisattivaFstab, _: Amministratore) -> dict[str, str]:
    """Commenta in `/etc/fstab` la riga di un montaggio ormai gestito dal pannello.

    Va fatto **dopo** aver importato e verificato il mount, non insieme: finché
    entrambi sono attivi il sistema prova a montare due volte lo stesso
    percorso, e chi si trova davanti l'errore non capisce da dove venga.

    La riga non viene cancellata ma commentata, dopo una copia di sicurezza del
    file: una riga sbagliata in `/etc/fstab` può impedire l'avvio della
    macchina, e chi ci si trova davanti deve poter capire cos'è successo.
    """
    try:
        return dict(await agent_client.chiedi("fstab.disable", {"mountpoint": dati.mountpoint}))
    except (agent_client.AgentNonDisponibile, agent_client.AgentRifiuta) as exc:
        raise errore_agent(exc) from exc


@router.get("/{mount_id}/cartelle", response_model=list[CartellaMount])
async def cartelle(
    mount_id: int,
    sessione: Sessione,
    _: Amministratore,
    percorso: str = Query(default="", max_length=1024),
) -> list[CartellaMount]:
    """Sottocartelle di un mount, per scegliere cosa pubblicare sfogliando.

    A differenza di `/archivio/{slug}` non serve una pubblicazione già
    creata: qui si guarda direttamente la condivisione NFS grezza, motivo per
    cui l'endpoint e' riservato agli amministratori invece di passare per
    l'ACL di uno share.
    """
    mount = await _carica(sessione, mount_id)
    try:
        normalizzato = str(normalizza_relativo(percorso))
        reale = risolvi(Path(mount.mountpoint), percorso)
    except PercorsoNonValido as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    try:
        voci = await archivio.elenca(reale, normalizzato, lambda _: True)
    except archivio.ArchivioNonDisponibile as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return [CartellaMount(nome=v.nome, percorso=v.percorso) for v in voci if v.cartella]


@router.get("/{mount_id}", response_model=MountDettaglio)
async def dettaglio(mount_id: int, sessione: Sessione, _: Amministratore) -> MountDettaglio:
    mount = await _carica(sessione, mount_id)
    stato = await servizio.leggi_stato(mount)
    if stato is not None:
        servizio.applica_stato(mount, stato)
        await sessione.commit()
    return await _dettaglio(mount)


@router.patch("/{mount_id}", response_model=MountDettaglio)
async def modifica(
    mount_id: int, dati: MountUpdate, sessione: Sessione, _: Amministratore
) -> MountDettaglio:
    mount = await _carica(sessione, mount_id)

    if dati.label is not None:
        mount.label = dati.label
    if dati.nfs_version is not None:
        mount.nfs_version = dati.nfs_version
    if dati.automount is not None:
        mount.automount = dati.automount
    if dati.idle_timeout is not None:
        mount.idle_timeout = dati.idle_timeout
    if dati.consenti_scrittura is not None:
        mount.requested_access = (
            AccessoNFS.LETTURA_SCRITTURA if dati.consenti_scrittura else AccessoNFS.SOLA_LETTURA
        )

    # La configurazione va riscritta e ricaricata, altrimenti la modifica
    # resterebbe solo nel database e il sistema continuerebbe come prima.
    try:
        await agent_client.chiedi("mount.create", servizio.dati_creazione(mount))
    except (agent_client.AgentNonDisponibile, agent_client.AgentRifiuta) as exc:
        raise errore_agent(exc) from exc

    await sessione.commit()
    await sessione.refresh(mount)
    return await _dettaglio(mount)


@router.post("/{mount_id}/avvia", response_model=MountDettaglio)
async def avvia(mount_id: int, sessione: Sessione, _: Amministratore) -> MountDettaglio:
    mount = await _carica(sessione, mount_id)
    try:
        stato = await agent_client.chiedi(
            "mount.start", {"slug": mount.slug, "automount": mount.automount}
        )
    except agent_client.AgentRifiuta as exc:
        mount.state = StatoMount.ERRORE
        mount.last_error = exc.messaggio
        await sessione.commit()
        raise errore_agent(exc) from exc
    except agent_client.AgentNonDisponibile as exc:
        raise errore_agent(exc) from exc

    servizio.applica_stato(mount, stato)
    await sessione.commit()
    return await _dettaglio(mount)


@router.post("/{mount_id}/ferma", response_model=MountDettaglio)
async def ferma(mount_id: int, sessione: Sessione, _: Amministratore) -> MountDettaglio:
    mount = await _carica(sessione, mount_id)
    try:
        stato = await agent_client.chiedi("mount.stop", {"slug": mount.slug})
    except (agent_client.AgentNonDisponibile, agent_client.AgentRifiuta) as exc:
        raise errore_agent(exc) from exc

    servizio.applica_stato(mount, stato)
    await sessione.commit()
    return await _dettaglio(mount)


@router.delete("/{mount_id}", status_code=status.HTTP_204_NO_CONTENT)
async def elimina(mount_id: int, sessione: Sessione, _: Amministratore) -> None:
    mount = await _carica(sessione, mount_id)
    try:
        await agent_client.chiedi("mount.remove", {"slug": mount.slug})
    except agent_client.AgentNonDisponibile as exc:
        # Non si cancella il record se il sistema non e stato ripulito:
        # resterebbero unit systemd orfane senza piu nulla che le rappresenti.
        raise errore_agent(exc) from exc
    except agent_client.AgentRifiuta as exc:
        raise errore_agent(exc) from exc

    await sessione.delete(mount)
    await sessione.commit()
