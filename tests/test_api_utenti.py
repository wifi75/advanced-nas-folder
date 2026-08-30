"""Test della gestione degli utenti.

Le prove che contano non sono creare ed elencare, ma le due protezioni che
impediscono di rendere il pannello ingestibile: non ci si può chiudere fuori
da soli, e l'ultimo amministratore non si tocca.
"""

import pytest
from app.api.v1.auth import PASSWORD_INIZIALE
from httpx import AsyncClient


@pytest.fixture(autouse=True)
async def database_pulito():  # noqa: ANN201
    yield
    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.models import User
    from sqlalchemy import delete, select, update

    async with SessionLocal() as sessione:
        await sessione.execute(delete(User).where(User.username != "admin"))

        # Questi test degradano, disattivano e perfino eliminano
        # l'amministratore per verificare le protezioni. Va rimesso com'era:
        # l'avvio dell'applicazione lo ricrea solo quando non c'è nessun
        # utente, e qui qualcuno resta quasi sempre.
        esistente = await sessione.execute(select(User).where(User.username == "admin"))
        if esistente.scalar_one_or_none() is None:
            sessione.add(
                User(
                    username="admin",
                    password_hash=hash_password(PASSWORD_INIZIALE),
                    is_admin=True,
                    is_active=True,
                )
            )
        else:
            await sessione.execute(
                update(User)
                .where(User.username == "admin")
                .values(
                    is_admin=True, is_active=True, password_hash=hash_password(PASSWORD_INIZIALE)
                )
            )
        await sessione.commit()


_NUOVO = {
    "username": "mario",
    "password": "una-password-lunga",
    "is_admin": False,
    "can_upload": True,
}


async def _crea(admin: AsyncClient, **extra: object) -> dict:
    risposta = await admin.post("/api/v1/utenti", json={**_NUOVO, **extra})
    assert risposta.status_code == 201, risposta.text
    return risposta.json()


# --- creazione -------------------------------------------------------------


async def test_crea_un_utente_e_puo_accedere(admin: AsyncClient) -> None:
    creato = await _crea(admin)
    assert creato["username"] == "mario"
    assert creato["can_upload"] is True

    accesso = await admin.post(
        "/api/v1/auth/login", json={"username": "mario", "password": "una-password-lunga"}
    )
    assert accesso.status_code == 200


async def test_la_password_non_torna_mai_indietro(admin: AsyncClient) -> None:
    creato = await _crea(admin)
    assert "password" not in creato
    assert "password_hash" not in creato


async def test_nome_gia_in_uso(admin: AsyncClient) -> None:
    await _crea(admin)
    risposta = await admin.post("/api/v1/utenti", json=_NUOVO)
    assert risposta.status_code == 409


async def test_password_troppo_corta_rifiutata(admin: AsyncClient) -> None:
    """È l'unica difesa di un pannello che espone cartelle di rete."""
    risposta = await admin.post("/api/v1/utenti", json={**_NUOVO, "password": "corta"})
    assert risposta.status_code == 422


async def test_ambito_con_risalita_rifiutato(admin: AsyncClient) -> None:
    """L'ambito è un confine: se lo si potesse scrivere come ../.. non lo sarebbe."""
    risposta = await admin.post("/api/v1/utenti", json={**_NUOVO, "scope": "../../etc"})
    assert risposta.status_code == 400


async def test_ambito_normalizzato(admin: AsyncClient) -> None:
    creato = await _crea(admin, scope="/foto/")
    assert creato["scope"] == "foto"


# --- modifica --------------------------------------------------------------


async def test_modifica_permessi_e_password(admin: AsyncClient) -> None:
    creato = await _crea(admin)
    risposta = await admin.patch(
        f"/api/v1/utenti/{creato['id']}",
        json={"can_delete": True, "password": "un-altra-password"},
    )
    assert risposta.status_code == 200
    assert risposta.json()["can_delete"] is True

    accesso = await admin.post(
        "/api/v1/auth/login", json={"username": "mario", "password": "un-altra-password"}
    )
    assert accesso.status_code == 200


async def test_disattivare_impedisce_laccesso(admin: AsyncClient) -> None:
    creato = await _crea(admin)
    await admin.patch(f"/api/v1/utenti/{creato['id']}", json={"is_active": False})

    accesso = await admin.post(
        "/api/v1/auth/login", json={"username": "mario", "password": "una-password-lunga"}
    )
    assert accesso.status_code == 401


# --- non chiudersi fuori ---------------------------------------------------


async def test_non_ci_si_puo_togliere_i_privilegi(admin: AsyncClient) -> None:
    io = (await admin.get("/api/v1/auth/me")).json()
    risposta = await admin.patch(f"/api/v1/utenti/{io['id']}", json={"is_admin": False})

    assert risposta.status_code == 400
    assert "te stesso" in risposta.json()["detail"]
    assert (await admin.get("/api/v1/auth/me")).json()["is_admin"] is True


async def test_non_ci_si_puo_disattivare(admin: AsyncClient) -> None:
    io = (await admin.get("/api/v1/auth/me")).json()
    risposta = await admin.patch(f"/api/v1/utenti/{io['id']}", json={"is_active": False})
    assert risposta.status_code == 400


async def test_non_ci_si_puo_eliminare(admin: AsyncClient) -> None:
    io = (await admin.get("/api/v1/auth/me")).json()
    risposta = await admin.delete(f"/api/v1/utenti/{io['id']}")
    assert risposta.status_code == 400


async def test_lultimo_amministratore_non_si_degrada(admin: AsyncClient) -> None:
    """Vale anche fatto da un altro amministratore: il risultato sarebbe lo stesso."""
    secondo = await _crea(admin, username="capo", is_admin=True)

    # Adesso ce ne sono due: togliere i privilegi al secondo è lecito.
    assert (
        await admin.patch(f"/api/v1/utenti/{secondo['id']}", json={"is_admin": False})
    ).status_code == 200

    # Torna amministratore, poi si prova a degradare il primo restando in due.
    await admin.patch(f"/api/v1/utenti/{secondo['id']}", json={"is_admin": True})

    accesso = await admin.post(
        "/api/v1/auth/login", json={"username": "capo", "password": "una-password-lunga"}
    )
    admin.headers["Authorization"] = f"Bearer {accesso.json()['access_token']}"

    # «capo» degrada l'admin originale: restando lui, è consentito.
    elenco = (await admin.get("/api/v1/utenti")).json()
    originale = next(u for u in elenco if u["username"] == "admin")
    assert (
        await admin.patch(f"/api/v1/utenti/{originale['id']}", json={"is_admin": False})
    ).status_code == 200

    # Ora «capo» è l'ultimo: non può degradare sé stesso né essere eliminato.
    io = (await admin.get("/api/v1/auth/me")).json()
    assert (
        await admin.patch(f"/api/v1/utenti/{io['id']}", json={"is_admin": False})
    ).status_code == 400


async def test_lultimo_amministratore_non_si_elimina(admin: AsyncClient) -> None:
    secondo = await _crea(admin, username="capo", is_admin=True)

    accesso = await admin.post(
        "/api/v1/auth/login", json={"username": "capo", "password": "una-password-lunga"}
    )
    admin.headers["Authorization"] = f"Bearer {accesso.json()['access_token']}"

    elenco = (await admin.get("/api/v1/utenti")).json()
    originale = next(u for u in elenco if u["username"] == "admin")
    assert (await admin.delete(f"/api/v1/utenti/{originale['id']}")).status_code == 204

    # «capo» è rimasto solo: cancellarlo lascerebbe il pannello ingestibile.
    assert (await admin.delete(f"/api/v1/utenti/{secondo['id']}")).status_code == 400


# --- password propria ------------------------------------------------------


async def test_cambio_password_richiede_quella_attuale(admin: AsyncClient) -> None:
    """Un token rubato non deve bastare a chiudere fuori il proprietario."""
    sbagliata = await admin.post(
        "/api/v1/utenti/me/password",
        json={"attuale": "non-e-questa", "nuova": "una-password-nuova"},
    )
    assert sbagliata.status_code == 400

    giusta = await admin.post(
        "/api/v1/utenti/me/password",
        json={"attuale": PASSWORD_INIZIALE, "nuova": "una-password-nuova"},
    )
    assert giusta.status_code == 204

    # Rimessa com'era, perché l'amministratore sopravvive ai test.
    accesso = await admin.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "una-password-nuova"}
    )
    admin.headers["Authorization"] = f"Bearer {accesso.json()['access_token']}"
    await admin.post(
        "/api/v1/utenti/me/password",
        json={"attuale": "una-password-nuova", "nuova": PASSWORD_INIZIALE},
    )


# --- permessi --------------------------------------------------------------


async def test_un_utente_normale_non_gestisce_gli_utenti(admin: AsyncClient) -> None:
    await _crea(admin)
    accesso = await admin.post(
        "/api/v1/auth/login", json={"username": "mario", "password": "una-password-lunga"}
    )
    admin.headers["Authorization"] = f"Bearer {accesso.json()['access_token']}"

    assert (await admin.get("/api/v1/utenti")).status_code == 403
    assert (await admin.post("/api/v1/utenti", json=_NUOVO)).status_code == 403
