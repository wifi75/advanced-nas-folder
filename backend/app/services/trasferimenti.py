"""Registro dei trasferimenti e IP reale di chi li fa.

Cosa questo registro sa e cosa no, perché è la differenza che rende
utilizzabile il monitoraggio invece che ingannevole:

* **sa** che un download è stato autorizzato, quando, per quale file, da chi e
  da quale indirizzo;
* **non sa**, da solo, quanti byte sono davvero arrivati né se il
  trasferimento è finito. La consegna è delegata al web server, e a quel punto
  l'applicazione è già uscita di scena.

I byte veri arrivano dal lettore dell'access log (`services/accesslog.py`),
quando è configurato. Finché non arrivano, `bytes_transferred` resta vuoto: un
numero inventato sarebbe peggio di un numero assente.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from ipaddress import ip_address
from typing import Any

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Transfer
from app.models.enums import StatoTrasferimento, TipoTrasferimento

#: Chi è in ascolto della dashboard. Ogni coda riceve gli eventi man mano che
#: succedono: è la parte "dal vivo" del monitoraggio.
_ascoltatori: set[asyncio.Queue[dict[str, Any]]] = set()

#: Oltre questo numero di eventi non letti l'ascoltatore viene considerato
#: fermo e i nuovi eventi vengono scartati per lui. Senza, una scheda lasciata
#: aperta in secondo piano farebbe crescere la memoria senza limite.
_CODA_MASSIMA = 200


def indirizzo_client(richiesta: Request) -> str | None:
    """Indirizzo reale del client, tenendo conto del reverse proxy.

    `X-Forwarded-For` viene letto **solo** se la richiesta arriva da un proxy
    dichiarato fidato: quell'intestazione la può scrivere chiunque, e fidarsene
    sempre significherebbe permettere a ogni visitatore di dichiarare l'IP che
    preferisce.
    """
    diretto = richiesta.client.host if richiesta.client else None
    if diretto is None:
        return None

    if diretto not in get_settings().trusted_proxy_list:
        return diretto

    inoltrato = richiesta.headers.get("x-forwarded-for", "")
    # Il primo della catena è il client originale; gli altri sono i proxy
    # attraversati.
    primo = inoltrato.split(",")[0].strip()
    if not primo:
        return diretto
    try:
        return str(ip_address(primo))
    except ValueError:
        # Un valore non interpretabile è un'intestazione costruita a mano: si
        # tiene l'indirizzo che si conosce per certo.
        return diretto


async def registra_download(
    sessione: AsyncSession,
    *,
    richiesta: Request,
    share_id: int | None,
    percorso: str,
    utente_id: int | None = None,
    link_id: int | None = None,
    dimensione: int | None = None,
) -> Transfer:
    """Annota che un download è stato autorizzato."""
    trasferimento = Transfer(
        kind=TipoTrasferimento.DOWNLOAD,
        status=StatoTrasferimento.IN_CORSO,
        share_id=share_id,
        user_id=utente_id,
        share_link_id=link_id,
        path=percorso,
        size=dimensione,
        client_ip=indirizzo_client(richiesta),
        user_agent=richiesta.headers.get("user-agent"),
        is_resumed="range" in richiesta.headers,
        started_at=datetime.now(UTC),
    )
    sessione.add(trasferimento)
    await sessione.commit()
    await sessione.refresh(trasferimento)

    annuncia(_evento(trasferimento))
    return trasferimento


async def registra_upload(
    sessione: AsyncSession,
    *,
    richiesta: Request,
    share_id: int | None,
    percorso: str,
    utente_id: int | None,
    dimensione: int,
) -> Transfer:
    """Annota un caricamento concluso.

    Qui il conteggio è certo, a differenza dei download: i byte sono passati
    dall'applicazione.
    """
    adesso = datetime.now(UTC)
    trasferimento = Transfer(
        kind=TipoTrasferimento.UPLOAD,
        status=StatoTrasferimento.COMPLETATO,
        share_id=share_id,
        user_id=utente_id,
        path=percorso,
        size=dimensione,
        bytes_transferred=dimensione,
        client_ip=indirizzo_client(richiesta),
        user_agent=richiesta.headers.get("user-agent"),
        started_at=adesso,
        finished_at=adesso,
    )
    sessione.add(trasferimento)
    await sessione.commit()
    await sessione.refresh(trasferimento)

    annuncia(_evento(trasferimento))
    return trasferimento


async def concludi(
    sessione: AsyncSession,
    percorso: str,
    *,
    client_ip: str | None,
    byte: int,
    stato: StatoTrasferimento,
) -> Transfer | None:
    """Chiude il download più recente che corrisponde, con i byte veri.

    La corrispondenza è per percorso e indirizzo, e prende il più recente
    ancora aperto: l'access log non contiene l'identificativo del
    trasferimento, quindi non c'è modo di fare meglio. Due download dello
    stesso file dallo stesso indirizzo nello stesso istante restano
    indistinguibili, ed è un limite accettabile per un contatore.
    """
    risultato = await sessione.execute(
        select(Transfer)
        .where(
            Transfer.kind == TipoTrasferimento.DOWNLOAD,
            Transfer.status == StatoTrasferimento.IN_CORSO,
            Transfer.path == percorso,
            Transfer.client_ip == client_ip,
        )
        .order_by(Transfer.started_at.desc())
        .limit(1)
    )
    trasferimento = risultato.scalar_one_or_none()
    if trasferimento is None:
        return None

    trasferimento.bytes_transferred = byte
    trasferimento.status = stato
    trasferimento.finished_at = datetime.now(UTC)
    await sessione.commit()
    await sessione.refresh(trasferimento)

    annuncia(_evento(trasferimento))
    return trasferimento


def _evento(trasferimento: Transfer) -> dict[str, Any]:
    return {
        "id": trasferimento.id,
        "tipo": trasferimento.kind.value,
        "stato": trasferimento.status.value,
        "percorso": trasferimento.path,
        "dimensione": trasferimento.size,
        "trasferiti": trasferimento.bytes_transferred,
        "client_ip": trasferimento.client_ip,
        "ripresa": trasferimento.is_resumed,
        "share_id": trasferimento.share_id,
        "utente_id": trasferimento.user_id,
        "iniziato": trasferimento.started_at.isoformat(),
        "concluso": (trasferimento.finished_at.isoformat() if trasferimento.finished_at else None),
    }


def annuncia(evento: dict[str, Any]) -> None:
    """Manda l'evento a chi sta guardando la dashboard."""
    for coda in list(_ascoltatori):
        if coda.qsize() >= _CODA_MASSIMA:
            continue
        coda.put_nowait(evento)


async def flusso() -> AsyncGenerator[dict[str, Any]]:
    """Eventi man mano che succedono, per un solo ascoltatore."""
    coda: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    _ascoltatori.add(coda)
    try:
        while True:
            yield await coda.get()
    finally:
        _ascoltatori.discard(coda)


async def recenti(sessione: AsyncSession, limite: int = 100) -> list[Transfer]:
    risultato = await sessione.execute(
        select(Transfer).order_by(Transfer.started_at.desc()).limit(limite)
    )
    return list(risultato.scalars().all())


@contextlib.contextmanager
def senza_ascoltatori() -> Any:
    """Svuota gli ascoltatori. Serve ai test, che non devono lasciarne in giro."""
    precedenti = set(_ascoltatori)
    _ascoltatori.clear()
    try:
        yield
    finally:
        _ascoltatori.clear()
        _ascoltatori.update(precedenti)
