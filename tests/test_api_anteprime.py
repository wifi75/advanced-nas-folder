"""Test dell'apertura in linea e del checksum.

L'apertura in linea è la funzione più facile da rendere pericolosa: far
interpretare al browser un file caricato da altri, nel contesto del pannello,
è cross-site scripting con un altro nome. I test qui servono soprattutto a
verificare che i tipi sbagliati restino allegati.
"""

import hashlib
from pathlib import Path
from typing import Any

import pytest
from app.core.config import get_settings
from app.services import agent_client
from httpx import AsyncClient


@pytest.fixture
def cartella(tmp_path: Path) -> Path:
    (tmp_path / "foto.jpg").write_bytes(b"\xff\xd8\xff" + b"x" * 500)
    (tmp_path / "nota.txt").write_text("una nota", encoding="utf-8")
    (tmp_path / "pagina.html").write_text("<script>alert(1)</script>", encoding="utf-8")
    (tmp_path / "disegno.svg").write_text("<svg onload='alert(1)'/>", encoding="utf-8")
    (tmp_path / "programma.exe").write_bytes(b"MZ" + b"\x00" * 100)
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
            "slug": "nas-vista",
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


async def _file(client: AsyncClient, nome: str, **extra: Any) -> Any:  # noqa: ANN401
    return await client.get("/api/v1/archivio/documenti/file", params={"percorso": nome, **extra})


# --- apertura in linea -----------------------------------------------------


async def test_unimmagine_si_apre_nel_pannello(admin: AsyncClient, share_id: int) -> None:
    risposta = await _file(admin, "foto.jpg", mostra=True)
    assert risposta.headers["content-disposition"].startswith("inline")
    assert risposta.headers["content-type"] == "image/jpeg"


async def test_senza_richiesta_esplicita_resta_un_allegato(
    admin: AsyncClient, share_id: int
) -> None:
    risposta = await _file(admin, "foto.jpg")
    assert risposta.headers["content-disposition"].startswith("attachment")


@pytest.mark.parametrize("nome", ["pagina.html", "disegno.svg"])
async def test_i_file_interpretabili_non_si_aprono_mai(
    admin: AsyncClient, share_id: int, nome: str
) -> None:
    """Chiederlo per un tipo qualunque farebbe eseguire nel pannello un file altrui."""
    risposta = await _file(admin, nome, mostra=True)
    assert risposta.headers["content-disposition"].startswith("attachment")
    assert risposta.headers["content-type"] == "application/octet-stream"


async def test_un_eseguibile_non_si_apre(admin: AsyncClient, share_id: int) -> None:
    risposta = await _file(admin, "programma.exe", mostra=True)
    assert risposta.headers["content-disposition"].startswith("attachment")


async def test_il_testo_semplice_si_apre(admin: AsyncClient, share_id: int) -> None:
    risposta = await _file(admin, "nota.txt", mostra=True)
    assert risposta.headers["content-disposition"].startswith("inline")


async def test_aprire_non_aggira_i_permessi(admin: AsyncClient, share_id: int) -> None:
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "foto.jpg", "visibility": "negata"},
    )
    admin.headers.pop("Authorization", None)

    risposta = await _file(admin, "foto.jpg", mostra=True)
    assert risposta.status_code == 403


# --- checksum --------------------------------------------------------------


async def test_checksum_di_un_file(admin: AsyncClient, share_id: int, cartella: Path) -> None:
    atteso = hashlib.sha256((cartella / "nota.txt").read_bytes()).hexdigest()

    risposta = await admin.post(
        "/api/v1/archivio/documenti/checksum", json={"percorso": "nota.txt"}
    )
    assert risposta.status_code == 200
    assert risposta.json() == {
        "percorso": "nota.txt",
        "algoritmo": "sha256",
        "valore": atteso,
        "dimensione": 8,
    }


async def test_checksum_di_una_cartella_non_ha_senso(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.post("/api/v1/archivio/documenti/checksum", json={"percorso": "."})
    assert risposta.status_code in (400, 404, 422)


async def test_checksum_rispetta_i_permessi(admin: AsyncClient, share_id: int) -> None:
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "nota.txt", "visibility": "utenti"},
    )
    admin.headers.pop("Authorization", None)

    risposta = await admin.post(
        "/api/v1/archivio/documenti/checksum", json={"percorso": "nota.txt"}
    )
    assert risposta.status_code == 403


# --- editor di testo -------------------------------------------------------


async def test_legge_un_file_di_testo(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.get("/api/v1/archivio/documenti/testo", params={"percorso": "nota.txt"})
    assert risposta.status_code == 200
    assert risposta.json()["contenuto"] == "una nota"
    assert risposta.json()["troncato"] is False


async def test_salva_un_file_di_testo(admin: AsyncClient, share_id: int, cartella: Path) -> None:
    risposta = await admin.post(
        "/api/v1/archivio/documenti/testo",
        json={"percorso": "nota.txt", "contenuto": "riscritta\nsu due righe"},
    )
    assert risposta.status_code == 200
    assert (cartella / "nota.txt").read_text(encoding="utf-8") == "riscritta\nsu due righe"


async def test_una_scrittura_non_lascia_file_di_appoggio(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    """Il file temporaneo serve a non troncare l'originale, non a restare lì."""
    await admin.post(
        "/api/v1/archivio/documenti/testo",
        json={"percorso": "nota.txt", "contenuto": "nuova"},
    )
    assert not list(cartella.glob("*.anf-scrittura"))


async def test_chi_puo_leggere_non_puo_riscrivere(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    admin.headers.pop("Authorization", None)

    risposta = await admin.post(
        "/api/v1/archivio/documenti/testo",
        json={"percorso": "nota.txt", "contenuto": "abusiva"},
    )
    assert risposta.status_code == 403
    assert (cartella / "nota.txt").read_text(encoding="utf-8") == "una nota"


async def test_una_cartella_non_si_riscrive_come_testo(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    (cartella / "sottocartella").mkdir()
    risposta = await admin.post(
        "/api/v1/archivio/documenti/testo",
        json={"percorso": "sottocartella", "contenuto": "x"},
    )
    assert risposta.status_code == 409
