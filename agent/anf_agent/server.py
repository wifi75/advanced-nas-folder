"""Server dell'agent: socket Unix locale, un messaggio JSON per riga.

L'agent non apre alcuna porta di rete. L'unica via d'ingresso e un socket Unix
con permessi 0660, di proprieta di root e del gruppo dell'applicazione: solo
l'API puo parlargli, e nessuno da fuori la macchina.
"""

from __future__ import annotations

import asyncio
import contextlib
import grp
import logging
import os
from pathlib import Path, PurePosixPath
from typing import Any

from anf_agent import nfs, systemd_units
from anf_agent.protocol import CodiceErrore, ErroreAgent, Richiesta, Risposta, Verbo
from anf_agent.validators import (
    mountpoint_per,
    valida_opzioni,
    valida_percorso_export,
    valida_server,
    valida_slug,
    valida_versione_nfs,
)

logger = logging.getLogger("anf.agent")

#: Oltre questa dimensione una richiesta viene rifiutata senza leggerla tutta.
LIMITE_RICHIESTA = 64 * 1024


class Agent:
    def __init__(self, radice_mount: PurePosixPath) -> None:
        self.radice = radice_mount

    def gestisci(self, richiesta: Richiesta) -> Risposta:
        """Esegue la richiesta. Sincrona: lancia processi esterni."""
        match richiesta.verbo:
            case Verbo.PING:
                return Risposta.successo({"pong": True})
            case Verbo.NFS_DISCOVER:
                return self._discover(richiesta.dati)
            case Verbo.MOUNT_CREATE:
                return self._crea(richiesta.dati)
            case Verbo.MOUNT_START:
                return self._avvia(richiesta.dati)
            case Verbo.MOUNT_STOP:
                return self._ferma(richiesta.dati)
            case Verbo.MOUNT_REMOVE:
                return self._rimuovi(richiesta.dati)
            case Verbo.MOUNT_STATUS:
                return self._stato(richiesta.dati)
            case Verbo.MOUNT_LIST:
                return self._elenca()

    # --- operazioni ---

    def _discover(self, dati: dict[str, Any]) -> Risposta:
        server = valida_server(dati.get("server"))
        return Risposta.successo(
            {
                "server": server,
                "esportazioni": nfs.elenca_esportazioni(server),
                "versioni": nfs.versioni_supportate(server),
            }
        )

    def _crea(self, dati: dict[str, Any]) -> Risposta:
        slug = valida_slug(dati.get("slug"))
        server = valida_server(dati.get("server"))
        export = valida_percorso_export(dati.get("export_path"))
        versione = valida_versione_nfs(dati.get("nfs_version"))
        automount = bool(dati.get("automount", True))
        idle = int(dati.get("idle_timeout", 600))
        opzioni = valida_opzioni(dati.get("opzioni"))

        mountpoint = mountpoint_per(slug, self.radice)

        # La versione arriva da un campo dedicato, gia validato: non la si
        # accetta dentro le opzioni libere.
        opzioni = [o for o in opzioni if not o.startswith("vers=")]
        opzioni.append(f"vers={versione}")

        unit = systemd_units.scrivi_unit(
            slug=slug,
            server=server,
            export=export,
            mountpoint=mountpoint,
            opzioni=opzioni,
            automount=automount,
            idle_timeout=idle,
        )
        return Risposta.successo(
            {"slug": slug, "mountpoint": str(mountpoint), "unit": unit, "opzioni": opzioni}
        )

    def _avvia(self, dati: dict[str, Any]) -> Risposta:
        slug = valida_slug(dati.get("slug"))
        mountpoint = mountpoint_per(slug, self.radice)
        automount = bool(dati.get("automount", True))
        suffisso = "automount" if automount else "mount"
        systemd_units.avvia(systemd_units.nome_unit(mountpoint, suffisso))
        return Risposta.successo(self._leggi_stato(mountpoint))

    def _ferma(self, dati: dict[str, Any]) -> Risposta:
        slug = valida_slug(dati.get("slug"))
        mountpoint = mountpoint_per(slug, self.radice)
        for suffisso in ("automount", "mount"):
            systemd_units.ferma(systemd_units.nome_unit(mountpoint, suffisso))
        return Risposta.successo(self._leggi_stato(mountpoint))

    def _rimuovi(self, dati: dict[str, Any]) -> Risposta:
        slug = valida_slug(dati.get("slug"))
        mountpoint = mountpoint_per(slug, self.radice)
        rimosse = systemd_units.rimuovi_unit(mountpoint)
        try:
            Path(mountpoint).rmdir()
        except OSError:
            # Cartella non vuota o inesistente: non e un errore. In nessun caso
            # si cancella ricorsivamente qualcosa sotto la radice dei mount.
            logger.info("%s non rimossa: non vuota o gia assente", mountpoint)
        return Risposta.successo({"slug": slug, "unit_rimosse": rimosse})

    def _stato(self, dati: dict[str, Any]) -> Risposta:
        slug = valida_slug(dati.get("slug"))
        mountpoint = mountpoint_per(slug, self.radice)
        return Risposta.successo(self._leggi_stato(mountpoint))

    def _elenca(self) -> Risposta:
        radice = Path(self.radice)
        if not radice.exists():
            return Risposta.successo({"mount": []})
        elenco = [
            {"slug": voce.name, **self._leggi_stato(PurePosixPath(self.radice / voce.name))}
            for voce in sorted(radice.iterdir())
            if voce.is_dir()
        ]
        return Risposta.successo({"mount": elenco})

    @staticmethod
    def _innesca(mountpoint: PurePosixPath) -> None:
        """Tocca il percorso per far scattare il montaggio su richiesta.

        Con `x-systemd.automount` il filesystem viene montato al primo accesso:
        senza questo passaggio lo stato risulterebbe sempre "non montato", che
        e vero ma inutile, perche basta guardarci dentro per montarlo.
        """
        # NAS irraggiungibile o percorso assente: lo stato letto subito dopo
        # dira com'e andata, qui non serve interrompere.
        with contextlib.suppress(OSError):
            next(iter(os.scandir(str(mountpoint))), None)

    def _leggi_stato(self, mountpoint: PurePosixPath) -> dict[str, Any]:
        self._innesca(mountpoint)
        stato = nfs.stato_montaggio(mountpoint)
        if stato["montato"]:
            stato["scrittura_verificata"] = nfs.prova_scrittura(mountpoint)
        else:
            stato["scrittura_verificata"] = None
        stato["mountpoint"] = str(mountpoint)
        return stato


async def _servi_client(
    lettore: asyncio.StreamReader, scrittore: asyncio.StreamWriter, agent: Agent
) -> None:
    try:
        while True:
            try:
                riga = await lettore.readuntil(b"\n")
            except asyncio.IncompleteReadError:
                return
            except asyncio.LimitOverrunError:
                scrittore.write(
                    Risposta.fallimento(
                        CodiceErrore.RICHIESTA_MALFORMATA, "Richiesta troppo grande."
                    ).a_json()
                )
                await scrittore.drain()
                return

            if not riga.strip():
                continue

            try:
                richiesta = Richiesta.da_json(riga)
                # Le operazioni lanciano processi esterni e possono attendere a
                # lungo un NAS che non risponde: eseguite fuori dal thread
                # dell'event loop, cosi una richiesta lenta non blocca le altre.
                risposta = await asyncio.to_thread(agent.gestisci, richiesta)
            except ErroreAgent as exc:
                risposta = Risposta.fallimento(exc.codice, exc.messaggio)
            except Exception:
                logger.exception("Errore non previsto nella gestione della richiesta")
                risposta = Risposta.fallimento(CodiceErrore.INTERNO, "Errore interno dell'agent.")

            scrittore.write(risposta.a_json())
            await scrittore.drain()
    finally:
        scrittore.close()


async def avvia_server(percorso_socket: Path, gruppo: str, radice_mount: PurePosixPath) -> None:
    percorso_socket.parent.mkdir(parents=True, exist_ok=True)
    percorso_socket.unlink(missing_ok=True)

    agent = Agent(radice_mount)
    server = await asyncio.start_unix_server(
        lambda r, w: _servi_client(r, w, agent), path=str(percorso_socket)
    )

    # Il socket e l'unica superficie esposta: va richiuso subito ai soli membri
    # del gruppo dell'applicazione.
    try:
        os.chown(percorso_socket, 0, grp.getgrnam(gruppo).gr_gid)
    except KeyError, PermissionError:
        logger.warning("Gruppo %r non trovato: il socket resta di root", gruppo)
    percorso_socket.chmod(0o660)

    logger.info("Agent in ascolto su %s (radice mount: %s)", percorso_socket, radice_mount)
    async with server:
        await server.serve_forever()
