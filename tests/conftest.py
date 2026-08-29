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
    risposta = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin"}
    )
    token = risposta.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
