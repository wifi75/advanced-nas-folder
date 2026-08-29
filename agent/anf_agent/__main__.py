"""Avvio dell'agent privilegiato.

    python -m anf_agent

La configurazione arriva dall'ambiente, che systemd popola con EnvironmentFile.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path, PurePosixPath

from anf_agent.server import avvia_server

PREDEFINITI = {
    "ANF_AGENT_SOCKET": "/run/anf/agent.sock",
    "ANF_MOUNT_ROOT": "/srv/nas",
    "ANF_AGENT_GROUP": "anf",
    "ANF_LOG_LEVEL": "INFO",
}


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("ANF_LOG_LEVEL", PREDEFINITI["ANF_LOG_LEVEL"]),
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        stream=sys.stderr,
    )
    logger = logging.getLogger("anf.agent")

    socket = Path(os.environ.get("ANF_AGENT_SOCKET", PREDEFINITI["ANF_AGENT_SOCKET"]))
    radice = PurePosixPath(os.environ.get("ANF_MOUNT_ROOT", PREDEFINITI["ANF_MOUNT_ROOT"]))
    gruppo = os.environ.get("ANF_AGENT_GROUP", PREDEFINITI["ANF_AGENT_GROUP"])

    if not radice.is_absolute():
        logger.error("ANF_MOUNT_ROOT deve essere un percorso assoluto: %s", radice)
        return 2

    if os.geteuid() != 0:
        logger.error(
            "L'agent deve girare da root: monta filesystem e ricarica systemd. "
            "Non aggirare questo controllo eseguendo l'API con privilegi elevati."
        )
        return 2

    Path(radice).mkdir(parents=True, exist_ok=True)

    try:
        asyncio.run(avvia_server(socket, gruppo, radice))
    except KeyboardInterrupt:
        logger.info("Agent arrestato")
    finally:
        socket.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
