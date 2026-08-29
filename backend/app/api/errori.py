"""Traduzione degli errori dell'agent in risposte HTTP.

Sta in un modulo proprio perche la usano piu router: mount e vhost fanno
richieste diverse allo stesso agent, e devono raccontarne i guasti allo stesso
modo.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from app.services import agent_client


def errore_agent(exc: Exception) -> HTTPException:
    """Traduce un problema dell'agent in una risposta comprensibile.

    Un rifiuto per validazione e un difetto del pannello, non dell'utente: gli
    si risponde 400 ma con il messaggio dell'agent, che dice quale valore non
    andava bene. Gli altri rifiuti sono problemi del sistema o del NAS, e vanno
    raccontati cosi come arrivano — spesso contengono testualmente l'esito del
    test di sintassi del web server, che e l'unica cosa che spiega davvero
    cosa correggere.
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
