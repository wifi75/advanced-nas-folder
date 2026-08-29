"""Gestione delle condivisioni NFS dal pannello."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import Amministratore, Sessione
from app.core.config import get_settings
from app.models import Mount
from app.models.enums import AccessoNFS, StatoMount
from app.schemas.mount import (
    MountCreate,
    MountDettaglio,
    MountOut,
    MountUpdate,
    ScopertaRichiesta,
    ScopertaRisposta,
    StatoEffettivo,
)
from app.services import agent_client
from app.services import mounts as servizio

router = APIRouter(prefix="/mounts", tags=["mount"])


def _errore_agent(exc: Exception) -> HTTPException:
    """Traduce un problema dell'agent in una risposta comprensibile.

    Un rifiuto per validazione e un difetto del pannello (500): l'utente non
    puo farci nulla e non deve vedersi dare la colpa. Gli altri rifiuti sono
    problemi del sistema o del NAS, e vanno raccontati.
    """
    if isinstance(exc, agent_client.AgentNonDisponibile):
        return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    if isinstance(exc, agent_client.AgentRifiuta):
        if exc.codice == "validazione":
            return HTTPException(
                status.HTTP_400_BAD_REQUEST, f"Richiesta non valida: {exc.messaggio}"
            )
        return HTTPException(status.HTTP_502_BAD_GATEWAY, exc.messaggio)
    return HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Errore interno.")


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
        raise _errore_agent(exc) from exc
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
        raise _errore_agent(exc) from exc

    mount.mountpoint = str(risultato.get("mountpoint") or mount.mountpoint)
    sessione.add(mount)
    await sessione.commit()
    await sessione.refresh(mount)
    return await _dettaglio(mount)


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
        raise _errore_agent(exc) from exc

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
        raise _errore_agent(exc) from exc
    except agent_client.AgentNonDisponibile as exc:
        raise _errore_agent(exc) from exc

    servizio.applica_stato(mount, stato)
    await sessione.commit()
    return await _dettaglio(mount)


@router.post("/{mount_id}/ferma", response_model=MountDettaglio)
async def ferma(mount_id: int, sessione: Sessione, _: Amministratore) -> MountDettaglio:
    mount = await _carica(sessione, mount_id)
    try:
        stato = await agent_client.chiedi("mount.stop", {"slug": mount.slug})
    except (agent_client.AgentNonDisponibile, agent_client.AgentRifiuta) as exc:
        raise _errore_agent(exc) from exc

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
        raise _errore_agent(exc) from exc
    except agent_client.AgentRifiuta as exc:
        raise _errore_agent(exc) from exc

    await sessione.delete(mount)
    await sessione.commit()
