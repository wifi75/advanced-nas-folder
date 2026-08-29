"""Test delle impostazioni del pannello e dello spazio disco."""

from pathlib import Path
from typing import Any

import pytest
from app.services import agent_client
from httpx import AsyncClient


@pytest.fixture
def cartella(tmp_path: Path) -> Path:
    (tmp_path / "visibile.txt").write_text("x", encoding="utf-8")
    (tmp_path / ".nascosto.txt").write_text("x", encoding="utf-8")
    (tmp_path / ".in-arrivo.bin.anf-parziale").write_text("x", encoding="utf-8")
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
async def database_pulito():  # noqa: ANN201
    yield
    from app.core.database import SessionLocal
    from app.models import Mount, Setting, Share
    from sqlalchemy import delete

    async with SessionLocal() as sessione:
        await sessione.execute(delete(Setting))
        await sessione.execute(delete(Share))
        await sessione.execute(delete(Mount))
        await sessione.commit()


@pytest.fixture
async def share_id(admin: AsyncClient) -> int:
    risposta = await admin.post(
        "/api/v1/mounts",
        json={
            "slug": "nas-imp",
            "label": "NAS di prova",
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
            "default_visibility": "pubblica",
        },
    )
    return int(risposta.json()["id"])


# --- impostazioni ----------------------------------------------------------


async def test_valori_predefiniti(admin: AsyncClient) -> None:
    risposta = await admin.get("/api/v1/impostazioni")
    assert risposta.json() == {
        "titolo": "Advanced NAS Folder",
        "sottotitolo": None,
        "logo_url": None,
        "mostra_nascosti": False,
    }


async def test_il_titolo_si_puo_cambiare(admin: AsyncClient) -> None:
    await admin.patch("/api/v1/impostazioni", json={"titolo": "Archivio di casa"})
    assert (await admin.get("/api/v1/impostazioni")).json()["titolo"] == "Archivio di casa"


async def test_un_titolo_vuoto_torna_al_predefinito(admin: AsyncClient) -> None:
    """Un pannello senza nome non è una scelta: è un campo svuotato per sbaglio."""
    await admin.patch("/api/v1/impostazioni", json={"titolo": "   "})
    assert (await admin.get("/api/v1/impostazioni")).json()["titolo"] == "Advanced NAS Folder"


async def test_le_impostazioni_si_leggono_senza_accedere(client: AsyncClient) -> None:
    """Titolo e logo disegnano la pagina di accesso: tenerli dietro
    l'autenticazione significherebbe mostrarla senza il marchio di chi la ospita."""
    assert (await client.get("/api/v1/impostazioni")).status_code == 200


async def test_solo_gli_amministratori_le_cambiano(client: AsyncClient) -> None:
    assert (await client.patch("/api/v1/impostazioni", json={"titolo": "x"})).status_code == 401


# --- file nascosti ---------------------------------------------------------


async def test_i_nascosti_restano_fuori_per_impostazione_predefinita(
    admin: AsyncClient, share_id: int
) -> None:
    elenco = (await admin.get("/api/v1/archivio/documenti")).json()
    assert [v["nome"] for v in elenco["voci"]] == ["visibile.txt"]


async def test_i_nascosti_compaiono_se_richiesto(admin: AsyncClient, share_id: int) -> None:
    await admin.patch("/api/v1/impostazioni", json={"mostra_nascosti": True})

    nomi = [v["nome"] for v in (await admin.get("/api/v1/archivio/documenti")).json()["voci"]]
    assert ".nascosto.txt" in nomi


async def test_i_caricamenti_a_meta_non_compaiono_mai(admin: AsyncClient, share_id: int) -> None:
    """Un file parziale non è un file: mostrarlo lo farebbe sembrare scaricabile."""
    await admin.patch("/api/v1/impostazioni", json={"mostra_nascosti": True})

    nomi = [v["nome"] for v in (await admin.get("/api/v1/archivio/documenti")).json()["voci"]]
    assert not any(n.endswith(".anf-parziale") for n in nomi)


# --- spazio disco ----------------------------------------------------------


async def test_spazio_delle_condivisioni(admin: AsyncClient, share_id: int) -> None:
    elenco = (await admin.get("/api/v1/impostazioni/spazio")).json()
    assert len(elenco) == 1
    assert elenco[0]["label"] == "NAS di prova"
    assert elenco[0]["totale"] > 0
    assert elenco[0]["libero"] > 0


async def test_una_condivisione_irraggiungibile_non_risulta_piena(
    admin: AsyncClient, share_id: int
) -> None:
    """Mostrare zero farebbe sembrare pieno un disco che semplicemente non risponde."""
    from app.core.database import SessionLocal
    from app.models import Mount
    from sqlalchemy import update

    async with SessionLocal() as sessione:
        await sessione.execute(update(Mount).values(mountpoint="/percorso/che/non/esiste"))
        await sessione.commit()

    elenco = (await admin.get("/api/v1/impostazioni/spazio")).json()
    assert elenco[0]["totale"] is None
    assert elenco[0]["libero"] is None


async def test_spazio_del_disco_del_pannello(admin: AsyncClient) -> None:
    risposta = await admin.get("/api/v1/impostazioni/spazio/pannello")
    assert risposta.status_code == 200
    assert risposta.json()["totale"] > 0
