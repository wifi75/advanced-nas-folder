"""Client verso l'agent privilegiato.

L'API non esegue mai operazioni di sistema: le chiede all'agent attraverso un
socket Unix locale. Questo modulo e l'unico punto di contatto fra i due.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger("anf.agent_client")

#: Oltre questo tempo si rinuncia. Deve essere piu alto dei timeout interni
#: dell'agent, altrimenti si scade qui mentre lui sta ancora lavorando.
TIMEOUT_PREDEFINITO = 120.0

LIMITE_RISPOSTA = 4 * 1024 * 1024


class AgentNonDisponibile(RuntimeError):
    """L'agent non risponde: non e in esecuzione, o il socket non e raggiungibile."""


class AgentRifiuta(RuntimeError):
    """L'agent ha risposto con un errore previsto.

    Non e un guasto: e l'agent che fa il suo lavoro, tipicamente rifiutando un
    valore non valido. Il codice permette all'API di distinguere un difetto del
    pannello da un problema del sistema o del NAS.
    """

    def __init__(self, codice: str, messaggio: str) -> None:
        super().__init__(messaggio)
        self.codice = codice
        self.messaggio = messaggio


async def chiedi(
    verbo: str, dati: dict[str, Any] | None = None, *, timeout: float = TIMEOUT_PREDEFINITO
) -> dict[str, Any]:
    """Invia una richiesta all'agent e restituisce il risultato.

    Solleva `AgentNonDisponibile` se non si riesce a parlargli, `AgentRifiuta`
    se risponde con un errore.
    """
    percorso = str(get_settings().agent_socket)
    richiesta = json.dumps({"verbo": verbo, "dati": dati or {}}).encode() + b"\n"

    apri = getattr(asyncio, "open_unix_connection", None)
    if apri is None:
        # I socket Unix non esistono su Windows: in sviluppo su quella
        # piattaforma l'agent non e raggiungibile, e va detto chiaramente
        # invece di fallire con un errore incomprensibile.
        raise AgentNonDisponibile(
            "I socket Unix non sono disponibili su questo sistema operativo: "
            "l'agent funziona solo su Linux."
        )

    try:
        lettore, scrittore = await asyncio.wait_for(apri(percorso), timeout=10)
    except (OSError, TimeoutError) as exc:
        raise AgentNonDisponibile(
            f"Agent non raggiungibile su {percorso}. Verifica che il servizio "
            "anf-agent sia in esecuzione."
        ) from exc

    try:
        scrittore.write(richiesta)
        await scrittore.drain()
        riga = await asyncio.wait_for(lettore.readline(), timeout=timeout)
    except (TimeoutError, OSError) as exc:
        raise AgentNonDisponibile(f"L'agent non ha risposto entro {timeout:.0f} secondi.") from exc
    finally:
        scrittore.close()
        # La chiusura puo fallire se l'agent ha gia lasciato cadere la
        # connessione: la risposta e stata letta, non c'e altro da fare.
        with contextlib.suppress(OSError):
            await scrittore.wait_closed()

    if not riga:
        raise AgentNonDisponibile("L'agent ha chiuso la connessione senza rispondere.")

    try:
        risposta = json.loads(riga)
    except json.JSONDecodeError as exc:
        raise AgentNonDisponibile("Risposta dell'agent non interpretabile.") from exc

    if not risposta.get("ok"):
        codice = str(risposta.get("codice") or "interno")
        messaggio = str(risposta.get("errore") or "Errore non specificato.")
        logger.warning("Agent ha rifiutato %s: [%s] %s", verbo, codice, messaggio)
        raise AgentRifiuta(codice, messaggio)

    risultato = risposta.get("risultato")
    return risultato if isinstance(risultato, dict) else {}


async def disponibile() -> bool:
    """Vero se l'agent risponde. Usato dagli endpoint di stato."""
    try:
        await chiedi("ping", timeout=5)
    except AgentNonDisponibile, AgentRifiuta:
        return False
    return True
