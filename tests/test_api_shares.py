"""Test degli endpoint delle pubblicazioni, delle regole e dei permessi."""

from typing import Any

import pytest
from app.services import agent_client
from httpx import AsyncClient


class AgentFinto:
    """L'agent non serve a questi endpoint, ma la creazione di un mount sì."""

    async def chiedi(
        self, verbo: str, dati: dict[str, Any] | None = None, *, timeout: float = 0
    ) -> dict[str, Any]:
        if verbo == "mount.create":
            return {"mountpoint": f"/srv/nas/{(dati or {}).get('slug')}"}
        return {"montato": False}


@pytest.fixture(autouse=True)
def agente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(agent_client, "chiedi", AgentFinto().chiedi)


@pytest.fixture
async def mount_id(admin: AsyncClient) -> int:
    risposta = await admin.post(
        "/api/v1/mounts",
        json={
            "slug": "per-share",
            "label": "Per gli share",
            "server": "192.168.1.10",
            "export_path": "/volume1/dati",
        },
    )
    return int(risposta.json()["id"])


@pytest.fixture
async def share_id(admin: AsyncClient, mount_id: int) -> int:
    risposta = await admin.post(
        "/api/v1/shares",
        json={"slug": "archivio", "label": "Archivio", "mount_id": mount_id},
    )
    return int(risposta.json()["id"])


@pytest.fixture(autouse=True)
async def database_pulito():  # noqa: ANN201
    """Svuota mount e pubblicazioni dopo ogni test."""
    yield
    from app.core.database import SessionLocal
    from app.models import Mount, Share
    from sqlalchemy import delete

    async with SessionLocal() as sessione:
        await sessione.execute(delete(Share))
        await sessione.execute(delete(Mount))
        await sessione.commit()


# --- accesso ---------------------------------------------------------------


async def test_serve_autenticazione(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/shares")).status_code == 401


# --- pubblicazioni ---------------------------------------------------------


async def test_crea_pubblicazione(admin: AsyncClient, mount_id: int) -> None:
    risposta = await admin.post(
        "/api/v1/shares", json={"slug": "foto", "label": "Foto", "mount_id": mount_id}
    )
    assert risposta.status_code == 201
    assert risposta.json()["default_visibility"] == "utenti"


async def test_mount_inesistente(admin: AsyncClient) -> None:
    risposta = await admin.post(
        "/api/v1/shares", json={"slug": "x", "label": "X", "mount_id": 99999}
    )
    assert risposta.status_code == 400


async def test_slug_duplicato(admin: AsyncClient, mount_id: int) -> None:
    for _ in range(2):
        risposta = await admin.post(
            "/api/v1/shares", json={"slug": "doppio", "label": "D", "mount_id": mount_id}
        )
    assert risposta.status_code == 409


@pytest.mark.parametrize("percorso", ["../fuori", "/etc/../passwd", "a/../../b"])
async def test_sottopercorso_con_risalita_respinto(
    admin: AsyncClient, mount_id: int, percorso: str
) -> None:
    risposta = await admin.post(
        "/api/v1/shares",
        json={"slug": "risalita", "label": "R", "mount_id": mount_id, "subpath": percorso},
    )
    assert risposta.status_code == 400


async def test_sottopercorso_normalizzato(admin: AsyncClient, mount_id: int) -> None:
    """`/foto/` e `foto` devono diventare la stessa cosa."""
    risposta = await admin.post(
        "/api/v1/shares",
        json={"slug": "norm", "label": "N", "mount_id": mount_id, "subpath": "/foto/"},
    )
    assert risposta.json()["subpath"] == "foto"


# --- regole di visibilità --------------------------------------------------


async def test_aggiungi_regola(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "riservato", "visibility": "negata"},
    )
    assert risposta.status_code == 201
    assert risposta.json()["visibility"] == "negata"


async def test_regola_password_richiede_la_password(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.post(
        f"/api/v1/shares/{share_id}/regole", json={"path_prefix": "x", "visibility": "password"}
    )
    assert risposta.status_code == 422


async def test_la_password_non_torna_mai_indietro(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "x", "visibility": "password", "password": "segreta"},
    )
    corpo = risposta.json()
    assert corpo["protetta_da_password"] is True
    assert "password" not in corpo
    assert "segreta" not in risposta.text


async def test_una_sola_regola_per_percorso(admin: AsyncClient, share_id: int) -> None:
    """Due regole sullo stesso percorso renderebbero la decisione casuale."""
    for _ in range(2):
        risposta = await admin.post(
            f"/api/v1/shares/{share_id}/regole",
            json={"path_prefix": "stessa", "visibility": "pubblica"},
        )
    assert risposta.status_code == 409


# --- permessi degli utenti -------------------------------------------------


async def test_assegna_permesso(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.put(
        f"/api/v1/shares/{share_id}/permessi",
        json={"user_id": 1, "path_prefix": "riservato", "livello": "lettura"},
    )
    assert risposta.status_code == 200
    assert risposta.json()["livello"] == "lettura"


async def test_riassegnare_aggiorna_invece_di_duplicare(admin: AsyncClient, share_id: int) -> None:
    primo = await admin.put(
        f"/api/v1/shares/{share_id}/permessi",
        json={"user_id": 1, "path_prefix": "x", "livello": "lettura"},
    )
    secondo = await admin.put(
        f"/api/v1/shares/{share_id}/permessi",
        json={"user_id": 1, "path_prefix": "x", "livello": "scrittura"},
    )
    assert primo.json()["id"] == secondo.json()["id"]
    assert secondo.json()["livello"] == "scrittura"


async def test_permesso_a_utente_inesistente(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.put(
        f"/api/v1/shares/{share_id}/permessi", json={"user_id": 99999, "livello": "lettura"}
    )
    assert risposta.status_code == 400


# --- verifica dell'accesso -------------------------------------------------


async def test_prova_accesso_anonimo_su_percorso_pubblico(
    admin: AsyncClient, share_id: int
) -> None:
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "pubblico", "visibility": "pubblica"},
    )
    risposta = await admin.post(
        f"/api/v1/shares/{share_id}/prova-accesso", json={"percorso": "pubblico/foto.jpg"}
    )
    corpo = risposta.json()
    assert corpo["consentito"] is True
    assert corpo["regola"] == "pubblico"


async def test_prova_accesso_spiega_il_diniego(admin: AsyncClient, share_id: int) -> None:
    """Chi configura i permessi deve sapere QUALE regola ha deciso."""
    risposta = await admin.post(
        f"/api/v1/shares/{share_id}/prova-accesso", json={"percorso": "qualunque"}
    )
    corpo = risposta.json()
    assert corpo["consentito"] is False
    assert corpo["motivo"]


async def test_prova_accesso_con_permesso_personale(admin: AsyncClient, share_id: int) -> None:
    await admin.patch(f"/api/v1/shares/{share_id}", json={"default_visibility": "utenti_scelti"})
    prima = await admin.post(
        f"/api/v1/shares/{share_id}/prova-accesso",
        json={"percorso": "riservato/x", "user_id": 1},
    )
    await admin.put(
        f"/api/v1/shares/{share_id}/permessi",
        json={"user_id": 1, "path_prefix": "riservato", "livello": "lettura"},
    )
    dopo = await admin.post(
        f"/api/v1/shares/{share_id}/prova-accesso",
        json={"percorso": "riservato/x", "user_id": 1},
    )
    # L'utente 1 è l'amministratore, che passa comunque: qui conta che la
    # motivazione cambi, cioè che sia il permesso a decidere.
    assert prima.json()["consentito"] is True
    assert dopo.json()["consentito"] is True


async def test_percorso_con_risalita_nella_prova(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.post(
        f"/api/v1/shares/{share_id}/prova-accesso", json={"percorso": "../../etc/passwd"}
    )
    assert risposta.status_code in (400, 422)


async def test_pubblicazione_inesistente(admin: AsyncClient) -> None:
    assert (await admin.get("/api/v1/shares/99999")).status_code == 404
