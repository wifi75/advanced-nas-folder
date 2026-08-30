"""Ambiente condiviso dai test.

Le variabili vanno impostate PRIMA di importare l'applicazione: la
configurazione viene letta una volta sola e memorizzata.
"""

import os
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest

_TEMPORANEA = Path(tempfile.mkdtemp(prefix="anf-test-"))

os.environ.update(
    {
        "ANF_ENV": "development",
        "ANF_SECRET_KEY": "chiave-di-prova-lunga-abbastanza-per-la-validazione",
        "ANF_DB_PATH": str(_TEMPORANEA / "prova.sqlite3"),
        "ANF_AGENT_SOCKET": str(_TEMPORANEA / "agent.sock"),
        "ANF_MOUNT_ROOT": str(_TEMPORANEA / "nas"),
    }
)


@pytest.fixture
async def client() -> AsyncGenerator:
    """Client HTTP collegato all'applicazione, senza aprire porte di rete."""
    from app.main import app
    from httpx import ASGITransport, AsyncClient

    # Il lifespan crea le tabelle e l'utente iniziale.
    async with (
        AsyncClient(transport=ASGITransport(app=app), base_url="http://prova") as c,
        app.router.lifespan_context(app),
    ):
        yield c


@pytest.fixture
async def admin(client):  # noqa: ANN001, ANN201 - tipo fornito dalla fixture client
    """Client gia autenticato come amministratore."""
    # L'import sta qui e non in cima: la configurazione si legge una volta
    # sola, e importare l'applicazione prima che le variabili d'ambiente
    # siano impostate la fisserebbe sui valori sbagliati.
    from app.api.v1.auth import PASSWORD_INIZIALE

    risposta = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": PASSWORD_INIZIALE},
    )
    token = risposta.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def anonimo(admin):  # noqa: ANN001, ANN201 - tipo fornito dalla fixture client
    """Un modo di fare richieste senza credenziali.

    Serve una funzione e non un secondo client: `admin` e `client` sono lo
    **stesso oggetto** — la fixture ci aggiunge l'intestazione — quindi
    chiedere entrambi in un test dava una richiesta «anonima» in realta'
    autenticata, e il test passava per il motivo sbagliato.
    """

    async def senza_credenziali(percorso: str, **kwargs: object):  # noqa: ANN003, ANN202
        # Le intestazioni passate alla singola richiesta si *sommano* a quelle
        # del client: per non mandare l'autorizzazione bisogna toglierla e poi
        # rimetterla, non sovrascriverla.
        token = admin.headers.pop("Authorization", None)
        try:
            return await admin.get(percorso, **kwargs)
        finally:
            if token is not None:
                admin.headers["Authorization"] = token

    return senza_credenziali


@pytest.fixture(autouse=True)
async def registro_pulito():  # noqa: ANN201
    """Svuota il registro dei trasferimenti dopo ogni test.

    Ogni download e ogni caricamento vi lasciano una riga, anche nei test che
    non se ne occupano: senza questa pulizia le prove sul monitoraggio
    contano anche le righe lasciate dai file di test eseguiti prima.
    """
    yield
    from app.core.database import SessionLocal
    from app.models import Transfer
    from sqlalchemy import delete
    from sqlalchemy.exc import OperationalError

    try:
        async with SessionLocal() as sessione:
            await sessione.execute(delete(Transfer))
            await sessione.commit()
    except OperationalError:
        # I test dell'agent non avviano l'applicazione, quindi le tabelle non
        # esistono: non c'e' nulla da ripulire e non e' un errore.
        pass
