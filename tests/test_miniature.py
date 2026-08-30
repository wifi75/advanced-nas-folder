"""Miniature delle immagini pubblicate."""

from pathlib import Path
from typing import Any

import pytest
from app.services import agent_client, miniature
from httpx import AsyncClient
from PIL import Image


@pytest.fixture
def cartella(tmp_path: Path) -> Path:
    """La cartella pubblicata. In una sottocartella, non in `tmp_path`: la
    cache delle miniature sta accanto, e mescolarle renderebbe il test che
    verifica la separazione incapace di fallire."""
    nas = tmp_path / "nas"
    nas.mkdir()
    Image.new("RGB", (1200, 900), (30, 90, 160)).save(nas / "foto.jpg", "JPEG")
    (nas / "documento.txt").write_text("non e' un'immagine", encoding="utf-8")
    return nas


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    return tmp_path / "cache"


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


@pytest.fixture
async def database_pulito():  # noqa: ANN201
    """Ripulisce dopo i test che creano una pubblicazione.

    Non `autouse`: i test del solo servizio non aprono il database, e imporre
    loro una connessione li farebbe fallire in chiusura per un motivo che non
    ha nulla a che vedere con quello che verificano.
    """
    yield
    from app.core.database import SessionLocal
    from app.models import Mount, Share
    from sqlalchemy import delete

    async with SessionLocal() as sessione:
        await sessione.execute(delete(Share))
        await sessione.execute(delete(Mount))
        await sessione.commit()


@pytest.fixture
async def share_id(admin: AsyncClient, database_pulito: None) -> int:
    mount = await admin.post(
        "/api/v1/mounts",
        json={
            "slug": "nas-foto",
            "label": "NAS",
            "server": "192.168.1.10",
            "export_path": "/volume1/foto",
        },
    )
    share = await admin.post(
        "/api/v1/shares",
        json={
            "slug": "foto",
            "label": "Foto",
            "mount_id": mount.json()["id"],
            "default_visibility": "pubblica",
        },
    )
    return int(share.json()["id"])


# --- il servizio ------------------------------------------------------------


def test_riduce_lato_massimo(cartella: Path, cache: Path) -> None:
    ridotta = miniature.produci(cartella / "foto.jpg", cache)

    with Image.open(ridotta) as immagine:
        assert max(immagine.size) == miniature.LATO


def test_la_seconda_volta_riusa_quella_gia_prodotta(cartella: Path, cache: Path) -> None:
    """E' il punto della cache: rigenerarla a ogni richiesta annullerebbe il
    vantaggio di non scaricare l'originale."""
    prima = miniature.produci(cartella / "foto.jpg", cache)
    quando = prima.stat().st_mtime_ns

    seconda = miniature.produci(cartella / "foto.jpg", cache)

    assert seconda == prima
    assert seconda.stat().st_mtime_ns == quando


def test_una_foto_sostituita_non_mostra_la_vecchia(cartella: Path, cache: Path) -> None:
    """Il nome in cache dipende da data e dimensione: cambiando il file cambia
    l'indirizzo, e nessuno puo' ricevere la miniatura di prima."""
    prima = miniature.produci(cartella / "foto.jpg", cache)

    Image.new("RGB", (400, 400), (200, 30, 30)).save(cartella / "foto.jpg", "JPEG")
    seconda = miniature.produci(cartella / "foto.jpg", cache)

    assert seconda != prima


def test_un_file_che_non_e_immagine_viene_rifiutato(cartella: Path, cache: Path) -> None:
    with pytest.raises(miniature.NonUnImmagine):
        miniature.produci(cartella / "documento.txt", cache)


def test_le_miniature_non_finiscono_sul_nas(cartella: Path, cache: Path) -> None:
    """Scriverle nel mount sporcherebbe le cartelle di chi le ha condivise, e
    richiederebbe un permesso di scrittura che di norma non c'e'."""
    miniature.produci(cartella / "foto.jpg", cache)

    assert list(cartella.glob("**/*.jpg")) == [cartella / "foto.jpg"]


# --- l'endpoint -------------------------------------------------------------


async def test_restituisce_un_jpeg(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.get("/api/v1/archivio/foto/miniatura", params={"percorso": "foto.jpg"})

    assert risposta.status_code == 200
    assert risposta.headers["content-type"] == "image/jpeg"


async def test_un_file_non_riducibile_da_415(admin: AsyncClient, share_id: int) -> None:
    """Non 404: il file esiste. Chi chiama deve mostrare l'icona del tipo."""
    risposta = await admin.get(
        "/api/v1/archivio/foto/miniatura", params={"percorso": "documento.txt"}
    )

    assert risposta.status_code == 415


async def test_una_risalita_nel_percorso_viene_rifiutata(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.get(
        "/api/v1/archivio/foto/miniatura", params={"percorso": "../../etc/passwd"}
    )

    assert risposta.status_code in (400, 403, 404)
