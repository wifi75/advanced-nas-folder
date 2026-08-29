"""Impostazioni del pannello e spazio disco.

Le impostazioni stanno nel database e non in un file: cambiarle
dall'interfaccia è il requisito di partenza del progetto, e un file andrebbe
riscritto dall'agent per un motivo che non lo giustifica.

Sono poche e dichiarate qui una per una, non un dizionario libero: un
contenitore aperto a qualunque chiave diventa in fretta un posto dove
finiscono valori che nessuno sa più chi legge.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import anyio
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import Amministratore, Sessione, UtenteFacoltativo
from app.core.config import get_settings
from app.models import Mount, Setting
from app.schemas.archivio import ImpostazioniOut, ImpostazioniUpdate, SpazioDisco

router = APIRouter(prefix="/impostazioni", tags=["impostazioni"])


@dataclass(frozen=True, slots=True)
class Nota:
    chiave: str
    predefinito: str
    descrizione: str


#: Le sole impostazioni riconosciute. Aggiungerne una è una modifica al
#: codice, di proposito.
_NOTE = (
    Nota("titolo", "Advanced NAS Folder", "Nome mostrato nel pannello e nel titolo della scheda"),
    Nota("sottotitolo", "", "Riga sotto il nome, facoltativa"),
    Nota("logo_url", "", "Indirizzo di un'immagine da usare al posto del nome"),
    Nota("mostra_nascosti", "no", "Se elencare anche i file che iniziano con un punto"),
)

_PREDEFINITI = {n.chiave: n.predefinito for n in _NOTE}


async def _leggi(sessione: Sessione) -> dict[str, str]:
    risultato = await sessione.execute(select(Setting))
    salvate = {s.key: s.value for s in risultato.scalars().all()}
    return {**_PREDEFINITI, **{k: v for k, v in salvate.items() if k in _PREDEFINITI}}


@router.get("", response_model=ImpostazioniOut)
async def leggi(sessione: Sessione, _: UtenteFacoltativo) -> ImpostazioniOut:
    """Le impostazioni del pannello.

    Leggibili anche senza accedere: il titolo e il logo servono a disegnare la
    pagina di accesso, e tenerli dietro l'autenticazione significherebbe
    mostrare quella pagina senza il marchio di chi la ospita.
    """
    valori = await _leggi(sessione)
    return ImpostazioniOut(
        titolo=valori["titolo"],
        sottotitolo=valori["sottotitolo"] or None,
        logo_url=valori["logo_url"] or None,
        mostra_nascosti=valori["mostra_nascosti"] == "si",
    )


@router.patch("", response_model=ImpostazioniOut)
async def modifica(
    dati: ImpostazioniUpdate, sessione: Sessione, _: Amministratore
) -> ImpostazioniOut:
    nuovi: dict[str, str] = {}
    if dati.titolo is not None:
        nuovi["titolo"] = dati.titolo.strip() or _PREDEFINITI["titolo"]
    if dati.sottotitolo is not None:
        nuovi["sottotitolo"] = dati.sottotitolo.strip()
    if dati.logo_url is not None:
        nuovi["logo_url"] = dati.logo_url.strip()
    if dati.mostra_nascosti is not None:
        nuovi["mostra_nascosti"] = "si" if dati.mostra_nascosti else "no"

    descrizioni = {n.chiave: n.descrizione for n in _NOTE}
    for chiave, valore in nuovi.items():
        esistente = await sessione.get(Setting, chiave)
        if esistente is None:
            sessione.add(Setting(key=chiave, value=valore, description=descrizioni[chiave]))
        else:
            esistente.value = valore

    await sessione.commit()
    return await leggi(sessione, None)


@router.get("/spazio", response_model=list[SpazioDisco])
async def spazio(sessione: Sessione, _: Amministratore) -> list[SpazioDisco]:
    """Spazio libero su ogni condivisione montata.

    Letto dal punto di montaggio, non chiesto al NAS: è il numero che conta,
    perché è quello che vede chi ci scrive. Una condivisione non raggiungibile
    non compare con zero — comparirebbe come piena, che è un'altra cosa — ma
    con lo spazio a `null`.
    """
    risultato = await sessione.execute(select(Mount).order_by(Mount.label))
    mounts = list(risultato.scalars().all())

    def misura(percorso: str) -> tuple[int, int] | None:
        try:
            uso = shutil.disk_usage(percorso)
        except OSError:
            return None
        return uso.total, uso.free

    letture: list[SpazioDisco] = []
    for mount in mounts:
        misurato = await anyio.to_thread.run_sync(misura, mount.mountpoint)
        letture.append(
            SpazioDisco(
                mount_id=mount.id,
                label=mount.label,
                mountpoint=mount.mountpoint,
                totale=misurato[0] if misurato else None,
                libero=misurato[1] if misurato else None,
            )
        )
    return letture


@router.get("/spazio/pannello", response_model=SpazioDisco)
async def spazio_pannello(_: Amministratore) -> SpazioDisco:
    """Spazio del disco su cui vive il pannello.

    Serve perché i caricamenti passano di lì solo di rimbalzo, ma il database e
    i log no: se si riempie questo disco il pannello smette di funzionare
    anche con il NAS mezzo vuoto.
    """
    radice = Path(get_settings().db_path).parent

    def misura() -> tuple[int, int] | None:
        try:
            uso = shutil.disk_usage(radice)
        except OSError:
            return None
        return uso.total, uso.free

    misurato = await anyio.to_thread.run_sync(misura)
    if misurato is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, f"Spazio non leggibile per {radice}."
        )
    return SpazioDisco(
        mount_id=None,
        label="pannello",
        mountpoint=str(radice),
        totale=misurato[0],
        libero=misurato[1],
    )
