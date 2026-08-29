"""Lettura del contenuto di una cartella pubblicata.

Il pannello elenca solo cio' che chi guarda ha davvero il diritto di vedere:
ogni voce viene passata al controllo degli accessi con il suo percorso
completo. Filtrare dopo, nell'interfaccia, non basterebbe — l'elenco arriva
comunque via API, e sarebbe leggibile da chiunque sappia aprirla.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

import anyio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Mount, PermessoUtente, Share, User
from app.services import acl
from app.services.percorsi import PercorsoNonValido, normalizza_relativo


class ArchivioNonDisponibile(RuntimeError):
    """La cartella pubblicata non e' leggibile: mount assente o caduto."""


@dataclass(frozen=True, slots=True)
class Voce:
    nome: str
    percorso: str
    cartella: bool
    dimensione: int | None
    modificato: datetime | None


async def radice(sessione: AsyncSession, share: Share) -> Path:
    """Cartella reale da cui parte la pubblicazione: mountpoint + sottopercorso."""
    mount = await sessione.get(Mount, share.mount_id)
    if mount is None:
        raise ArchivioNonDisponibile("La condivisione di origine non esiste piu'.")
    return Path(mount.mountpoint) / PurePosixPath(share.subpath or "")


async def carica_per_slug(sessione: AsyncSession, slug: str) -> Share | None:
    risultato = await sessione.execute(
        select(Share).where(Share.slug == slug).options(selectinload(Share.rules))
    )
    return risultato.scalar_one_or_none()


async def permessi_di(
    sessione: AsyncSession, share_id: int, utente: User | None
) -> list[PermessoUtente]:
    """I permessi personali dell'utente su questa pubblicazione."""
    if utente is None:
        return []
    risultato = await sessione.execute(
        select(PermessoUtente).where(
            PermessoUtente.share_id == share_id, PermessoUtente.user_id == utente.id
        )
    )
    return list(risultato.scalars().all())


def _leggi_cartella(reale: Path, base: PurePosixPath) -> list[Voce]:
    """Legge le voci dal disco. Sincrona: la chiama un thread separato.

    Una `stat` su NFS puo' fermarsi per secondi se il NAS non risponde, e
    farlo sul ciclo di eventi bloccherebbe tutte le altre richieste.
    """
    voci: list[Voce] = []
    with os.scandir(reale) as elenco:
        for elemento in elenco:
            if elemento.name.startswith("."):
                continue
            try:
                info = elemento.stat()
                cartella = elemento.is_dir()
            except OSError:
                # Un file sparito o illeggibile non deve far fallire l'elenco:
                # la cartella resta consultabile, quella voce semplicemente non
                # c'e'.
                continue
            voci.append(
                Voce(
                    nome=elemento.name,
                    percorso=str(base / elemento.name),
                    cartella=cartella,
                    dimensione=None if cartella else info.st_size,
                    modificato=datetime.fromtimestamp(info.st_mtime, UTC),
                )
            )
    return voci


async def elenca(
    reale: Path,
    percorso: str,
    share: Share,
    utente: User | None,
    permessi: list[PermessoUtente],
) -> list[Voce]:
    """Voci della cartella che l'utente puo' vedere, cartelle prima.

    Il controllo e' per singola voce: una sottocartella negata sparisce
    dall'elenco anche quando quella che la contiene e' aperta a tutti.
    """
    if not reale.is_dir():
        raise ArchivioNonDisponibile("La cartella non e' disponibile.")

    base = normalizza_relativo(percorso)
    try:
        voci = await anyio.to_thread.run_sync(_leggi_cartella, reale, base)
    except OSError as exc:
        raise ArchivioNonDisponibile("La cartella non e' leggibile.") from exc

    visibili = [
        v
        for v in voci
        if acl.valuta(share, v.percorso, utente, permessi=permessi).consentito
        and acl.dentro_ambito(utente, v.percorso)
    ]
    visibili.sort(key=lambda v: (not v.cartella, v.nome.casefold()))
    return visibili


def briciole(percorso: str) -> list[tuple[str, str]]:
    """Nome e percorso di ogni cartella attraversata, per la navigazione."""
    try:
        parti = normalizza_relativo(percorso).parts
    except PercorsoNonValido:
        return []
    return [(nome, "/".join(parti[: i + 1])) for i, nome in enumerate(parti)]
