"""Test della ricerca e del download di una cartella come archivio.

In entrambi i casi il punto delicato è lo stesso: né i risultati né l'archivio
devono contenere ciò che chi guarda non ha il diritto di vedere. Una ricerca
che mostrasse i nomi dentro una cartella vietata sarebbe un modo di leggerne
il contenuto; uno ZIP che li includesse sarebbe peggio.
"""

import io
import zipfile
from pathlib import Path
from typing import Any

import pytest
from app.services import agent_client
from httpx import AsyncClient


@pytest.fixture
def cartella(tmp_path: Path) -> Path:
    (tmp_path / "relazione-2026.txt").write_text("pubblico", encoding="utf-8")
    (tmp_path / "foto").mkdir()
    (tmp_path / "foto" / "relazione-foto.txt").write_text("anche questo", encoding="utf-8")
    (tmp_path / "foto" / "mare.txt").write_text("mare", encoding="utf-8")
    (tmp_path / "riservata").mkdir()
    (tmp_path / "riservata" / "relazione-segreta.txt").write_text("no", encoding="utf-8")
    (tmp_path / ".nascosto.txt").write_text("mai", encoding="utf-8")
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
    from app.models import Mount, Share
    from sqlalchemy import delete

    async with SessionLocal() as sessione:
        await sessione.execute(delete(Share))
        await sessione.execute(delete(Mount))
        await sessione.commit()


@pytest.fixture
async def share_id(admin: AsyncClient) -> int:
    risposta = await admin.post(
        "/api/v1/mounts",
        json={
            "slug": "nas-cerca",
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
            "default_visibility": "pubblica",
        },
    )
    return int(risposta.json()["id"])


def _anonimo(client: AsyncClient) -> AsyncClient:
    client.headers.pop("Authorization", None)
    return client


async def _vieta(admin: AsyncClient, share_id: int, percorso: str) -> None:
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": percorso, "visibility": "negata"},
    )


# --- ricerca ---------------------------------------------------------------


async def test_trova_nelle_sottocartelle(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.get("/api/v1/archivio/documenti/cerca", params={"q": "relazione"})
    assert risposta.status_code == 200

    percorsi = [v["percorso"] for v in risposta.json()["voci"]]
    assert "relazione-2026.txt" in percorsi
    assert "foto/relazione-foto.txt" in percorsi


async def test_la_ricerca_ignora_maiuscole_e_accenti_composti(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    (cartella / "Città.txt").write_text("x", encoding="utf-8")

    risposta = await admin.get("/api/v1/archivio/documenti/cerca", params={"q": "CITTÀ"})
    assert [v["nome"] for v in risposta.json()["voci"]] == ["Città.txt"]


async def test_la_ricerca_non_mostra_le_cartelle_vietate(admin: AsyncClient, share_id: int) -> None:
    await _vieta(admin, share_id, "riservata")

    risposta = await _anonimo(admin).get(
        "/api/v1/archivio/documenti/cerca", params={"q": "relazione"}
    )
    percorsi = [v["percorso"] for v in risposta.json()["voci"]]
    assert "riservata/relazione-segreta.txt" not in percorsi
    assert "relazione-2026.txt" in percorsi


async def test_la_ricerca_ignora_i_file_nascosti(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.get("/api/v1/archivio/documenti/cerca", params={"q": "nascosto"})
    assert risposta.json()["voci"] == []


async def test_ricerca_limitata_a_una_sottocartella(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.get(
        "/api/v1/archivio/documenti/cerca", params={"q": "relazione", "percorso": "foto"}
    )
    assert [v["percorso"] for v in risposta.json()["voci"]] == ["foto/relazione-foto.txt"]


async def test_un_solo_carattere_non_e_una_ricerca(admin: AsyncClient, share_id: int) -> None:
    """Con un carattere il risultato sarebbe mezzo archivio, a costo di un giro di rete
    per ogni cartella."""
    risposta = await admin.get("/api/v1/archivio/documenti/cerca", params={"q": "r"})
    assert risposta.status_code == 422


# --- archivio ZIP ----------------------------------------------------------


async def _zip(client: AsyncClient, **params: str) -> zipfile.ZipFile:
    risposta = await client.get("/api/v1/archivio/documenti/zip", params=params)
    assert risposta.status_code == 200, risposta.text
    assert risposta.headers["content-type"] == "application/zip"
    return zipfile.ZipFile(io.BytesIO(risposta.content))


async def test_scarica_una_cartella_come_zip(admin: AsyncClient, share_id: int) -> None:
    archivio = await _zip(admin, percorso="foto")
    assert sorted(archivio.namelist()) == ["mare.txt", "relazione-foto.txt"]
    assert archivio.read("mare.txt") == b"mare"


async def test_lo_zip_della_radice_contiene_i_percorsi_relativi(
    admin: AsyncClient, share_id: int
) -> None:
    archivio = await _zip(admin, percorso="")
    assert "foto/mare.txt" in archivio.namelist()
    assert "relazione-2026.txt" in archivio.namelist()


async def test_lo_zip_non_contiene_le_cartelle_vietate(admin: AsyncClient, share_id: int) -> None:
    await _vieta(admin, share_id, "riservata")

    archivio = await _zip(_anonimo(admin), percorso="")
    assert not any(n.startswith("riservata/") for n in archivio.namelist())
    assert "relazione-2026.txt" in archivio.namelist()


async def test_lo_zip_non_contiene_i_file_nascosti(admin: AsyncClient, share_id: int) -> None:
    archivio = await _zip(admin, percorso="")
    assert ".nascosto.txt" not in archivio.namelist()


async def test_il_nome_proposto_e_quello_della_cartella(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.get("/api/v1/archivio/documenti/zip", params={"percorso": "foto"})
    assert 'filename="foto.zip"' in risposta.headers["content-disposition"]


async def test_un_file_non_si_scarica_come_cartella(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.get(
        "/api/v1/archivio/documenti/zip", params={"percorso": "relazione-2026.txt"}
    )
    assert risposta.status_code == 404


async def test_lo_zip_di_una_cartella_riservata_e_negato(admin: AsyncClient, share_id: int) -> None:
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "riservata", "visibility": "utenti"},
    )
    risposta = await _anonimo(admin).get(
        "/api/v1/archivio/documenti/zip", params={"percorso": "riservata"}
    )
    assert risposta.status_code == 403
