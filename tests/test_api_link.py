"""Test dei link di condivisione: creazione, limiti, revoca e accesso."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from app.core.config import get_settings
from app.services import agent_client
from httpx import AsyncClient


@pytest.fixture
def cartella(tmp_path: Path) -> Path:
    (tmp_path / "pubblico.txt").write_text("visibile a tutti", encoding="utf-8")
    (tmp_path / "contabilita").mkdir()
    (tmp_path / "contabilita" / "bilancio.txt").write_text("riservato", encoding="utf-8")
    (tmp_path / "foto").mkdir()
    (tmp_path / "foto" / "mare.txt").write_text("una foto", encoding="utf-8")
    return tmp_path


@pytest.fixture(autouse=True)
def agente(monkeypatch: pytest.MonkeyPatch, cartella: Path) -> None:
    class AgentFinto:
        async def chiedi(
            self, verbo: str, dati: dict[str, Any] | None = None, *, timeout: float = 0
        ) -> dict[str, Any]:
            if verbo == "mount.create":
                return {"mountpoint": str(cartella)}
            return {"montato": True}

    monkeypatch.setattr(agent_client, "chiedi", AgentFinto().chiedi)


@pytest.fixture(autouse=True)
def consegna_in_locale(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "download_backend", "stream")


@pytest.fixture(autouse=True)
async def database_pulito():  # noqa: ANN201
    yield
    from app.core.database import SessionLocal
    from app.models import Mount, Share, ShareLink
    from sqlalchemy import delete

    async with SessionLocal() as sessione:
        await sessione.execute(delete(ShareLink))
        await sessione.execute(delete(Share))
        await sessione.execute(delete(Mount))
        await sessione.commit()


@pytest.fixture
async def share_id(admin: AsyncClient) -> int:
    risposta = await admin.post(
        "/api/v1/mounts",
        json={
            "slug": "nas-link",
            "label": "NAS",
            "server": "192.168.1.10",
            "export_path": "/volume1/dati",
        },
    )
    risposta = await admin.post(
        "/api/v1/shares",
        json={
            "slug": "documenti",
            "label": "Documenti",
            "mount_id": risposta.json()["id"],
            "default_visibility": "utenti",
        },
    )
    return int(risposta.json()["id"])


def _anonimo(client: AsyncClient) -> AsyncClient:
    client.headers.pop("Authorization", None)
    return client


async def _crea(admin: AsyncClient, share_id: int, **dati: Any) -> dict[str, Any]:
    risposta = await admin.post(f"/api/v1/shares/{share_id}/link", json=dati)
    assert risposta.status_code == 201, risposta.text
    return risposta.json()


# --- creazione -------------------------------------------------------------


async def test_il_token_viene_mostrato_una_volta_sola(admin: AsyncClient, share_id: int) -> None:
    creato = await _crea(admin, share_id, percorso="")
    assert creato["token"]

    # Nell'elenco il token non c'è più: nel database ne resta solo l'impronta.
    elenco = await admin.get(f"/api/v1/shares/{share_id}/link")
    assert elenco.json()[0].get("token") is None


async def test_un_link_apre_una_cartella_riservata(admin: AsyncClient, share_id: int) -> None:
    """La pubblicazione è riservata agli utenti: senza link un anonimo non entra."""
    negato = await _anonimo(admin).get("/api/v1/archivio/documenti")
    assert negato.status_code == 403

    # Il client è ormai anonimo: per creare il link serve di nuovo l'admin.
    accesso = await admin.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin"}
    )
    admin.headers["Authorization"] = f"Bearer {accesso.json()['access_token']}"

    creato = await _crea(admin, share_id, percorso="")
    risposta = await _anonimo(admin).get(f"/api/v1/link/{creato['token']}")
    assert risposta.status_code == 200
    assert "pubblico.txt" in [v["nome"] for v in risposta.json()["voci"]]


# --- limiti ----------------------------------------------------------------


async def test_il_link_non_porta_fuori_dal_suo_ramo(admin: AsyncClient, share_id: int) -> None:
    creato = await _crea(admin, share_id, percorso="foto")
    anonimo = _anonimo(admin)

    dentro = await anonimo.get(f"/api/v1/link/{creato['token']}", params={"percorso": "foto"})
    assert dentro.status_code == 200

    # Un ramo diverso non esiste, per chi ha questo token.
    fuori = await anonimo.get(f"/api/v1/link/{creato['token']}", params={"percorso": "contabilita"})
    assert fuori.status_code == 404


async def test_un_divieto_esplicito_batte_il_link(admin: AsyncClient, share_id: int) -> None:
    """Se un link superasse un divieto, crearne uno sarebbe il modo per aggirarlo."""
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "contabilita", "visibility": "negata"},
    )
    creato = await _crea(admin, share_id, percorso="")

    risposta = await _anonimo(admin).get(
        f"/api/v1/link/{creato['token']}", params={"percorso": "contabilita"}
    )
    assert risposta.status_code == 403


async def test_la_cartella_negata_sparisce_anche_dallelenco_del_link(
    admin: AsyncClient, share_id: int
) -> None:
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "contabilita", "visibility": "negata"},
    )
    creato = await _crea(admin, share_id, percorso="")

    risposta = await _anonimo(admin).get(f"/api/v1/link/{creato['token']}")
    assert "contabilita" not in [v["nome"] for v in risposta.json()["voci"]]


async def test_il_limite_di_scaricamenti_chiude_il_link(admin: AsyncClient, share_id: int) -> None:
    creato = await _crea(admin, share_id, percorso="", max_download=1)
    anonimo = _anonimo(admin)
    indirizzo = f"/api/v1/link/{creato['token']}/file"

    primo = await anonimo.get(indirizzo, params={"percorso": "pubblico.txt"})
    assert primo.status_code == 200
    assert primo.text == "visibile a tutti"

    secondo = await anonimo.get(indirizzo, params={"percorso": "pubblico.txt"})
    assert secondo.status_code == 403


async def test_un_link_scaduto_non_apre_piu(admin: AsyncClient, share_id: int) -> None:
    creato = await _crea(admin, share_id, percorso="", giorni=1)

    # Si sposta indietro la scadenza invece di aspettare un giorno.
    from app.core.database import SessionLocal
    from app.models import ShareLink

    async with SessionLocal() as sessione:
        collegamento = await sessione.get(ShareLink, creato["id"])
        assert collegamento is not None
        collegamento.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        await sessione.commit()

    risposta = await _anonimo(admin).get(f"/api/v1/link/{creato['token']}")
    assert risposta.status_code == 403


async def test_la_password_del_link_e_richiesta(admin: AsyncClient, share_id: int) -> None:
    creato = await _crea(admin, share_id, percorso="", password="segreto")
    anonimo = _anonimo(admin)

    senza = await anonimo.get(f"/api/v1/link/{creato['token']}")
    assert senza.status_code == 401

    con = await anonimo.get(f"/api/v1/link/{creato['token']}", params={"password": "segreto"})
    assert con.status_code == 200


# --- revoca ----------------------------------------------------------------


async def test_la_revoca_chiude_il_link_ma_ne_conserva_il_conteggio(
    admin: AsyncClient, share_id: int
) -> None:
    creato = await _crea(admin, share_id, percorso="")
    anonimo = _anonimo(admin)
    await anonimo.get(f"/api/v1/link/{creato['token']}/file", params={"percorso": "pubblico.txt"})

    accesso = await admin.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin"}
    )
    admin.headers["Authorization"] = f"Bearer {accesso.json()['access_token']}"

    revocato = await admin.delete(f"/api/v1/shares/{share_id}/link/{creato['id']}")
    assert revocato.status_code == 200
    # Quante volte è stato usato un collegamento poi revocato è esattamente
    # ciò che si vuole sapere dopo averlo revocato.
    assert revocato.json()["download_count"] == 1
    assert revocato.json()["is_revoked"] is True

    risposta = await _anonimo(admin).get(f"/api/v1/link/{creato['token']}")
    assert risposta.status_code == 403


async def test_un_token_inesistente_non_dice_nulla(admin: AsyncClient, share_id: int) -> None:
    risposta = await _anonimo(admin).get("/api/v1/link/token-inventato")
    assert risposta.status_code == 404
