"""Test degli endpoint di stato e autenticazione."""

from app.api.v1.auth import PASSWORD_INIZIALE
from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    risposta = await client.get("/api/v1/health")
    assert risposta.status_code == 200
    corpo = risposta.json()
    assert corpo["status"] == "ok"
    assert corpo["author"] == "Tiziano Cassone"
    assert corpo["version"]


async def test_health_ready_verifica_il_database(client: AsyncClient) -> None:
    risposta = await client.get("/api/v1/health/ready")
    assert risposta.status_code == 200
    assert risposta.json()["database"] == "ok"


async def test_accesso_con_utente_iniziale(client: AsyncClient) -> None:
    risposta = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": PASSWORD_INIZIALE}
    )
    assert risposta.status_code == 200
    corpo = risposta.json()
    assert corpo["user"]["is_admin"] is True
    assert corpo["access_token"]
    # Deve segnalare che la password e ancora quella iniziale.
    assert corpo["password_predefinita"] is True


async def test_password_sbagliata(client: AsyncClient) -> None:
    risposta = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "sbagliata"}
    )
    assert risposta.status_code == 401


async def test_utente_inesistente_stesso_errore(client: AsyncClient) -> None:
    """Non deve essere possibile capire quali utenti esistono."""
    inesistente = await client.post(
        "/api/v1/auth/login", json={"username": "nessuno", "password": "qualunque"}
    )
    sbagliata = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "sbagliata"}
    )
    assert inesistente.status_code == sbagliata.status_code == 401
    assert inesistente.json()["detail"] == sbagliata.json()["detail"]


async def test_endpoint_protetto_senza_token(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_endpoint_protetto_con_token_falso(client: AsyncClient) -> None:
    risposta = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer non-valido"})
    assert risposta.status_code == 401


async def test_endpoint_protetto_con_token_valido(client: AsyncClient) -> None:
    accesso = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": PASSWORD_INIZIALE}
    )
    token = accesso.json()["access_token"]
    risposta = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert risposta.status_code == 200
    assert risposta.json()["username"] == "admin"
