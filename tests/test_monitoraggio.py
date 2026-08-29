"""Test del registro dei trasferimenti e della lettura dell'access log.

Il punto delicato è l'indirizzo del client: `X-Forwarded-For` la può scrivere
chiunque, e fidarsene sempre significherebbe permettere a ogni visitatore di
dichiarare l'IP che preferisce.
"""

from pathlib import Path
from typing import Any

import pytest
from app.core.config import get_settings
from app.models.enums import StatoTrasferimento
from app.services import accesslog, agent_client
from httpx import AsyncClient


@pytest.fixture
def cartella(tmp_path: Path) -> Path:
    (tmp_path / "relazione.txt").write_text("dodici byte", encoding="utf-8")
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
            "slug": "nas-mon",
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


# --- registro --------------------------------------------------------------


async def test_un_download_viene_annotato(admin: AsyncClient, share_id: int) -> None:
    await admin.get("/api/v1/archivio/documenti/file", params={"percorso": "relazione.txt"})

    elenco = (await admin.get("/api/v1/trasferimenti")).json()
    assert len(elenco) == 1
    assert elenco[0]["path"] == "relazione.txt"
    assert elenco[0]["kind"] == "download"
    # I byte trasferiti restano vuoti: li conosce solo il web server.
    assert elenco[0]["bytes_transferred"] is None
    assert elenco[0]["size"] == 11


async def test_un_caricamento_viene_annotato_con_i_byte(admin: AsyncClient, share_id: int) -> None:
    """Qui il conteggio è certo: i byte sono passati dall'applicazione."""
    await admin.put(
        "/api/v1/archivio/documenti/carica",
        params={"nome": "nuovo.txt", "offset": 0, "percorso": ""},
        content=b"dodici byte!",
    )
    await admin.post(
        "/api/v1/archivio/documenti/carica/completa",
        json={"percorso": "", "nome": "nuovo.txt", "dimensione": 12},
    )

    elenco = (await admin.get("/api/v1/trasferimenti")).json()
    caricamento = next(t for t in elenco if t["kind"] == "upload")
    assert caricamento["bytes_transferred"] == 12
    assert caricamento["status"] == "completato"


async def test_una_ripresa_viene_riconosciuta(admin: AsyncClient, share_id: int) -> None:
    await admin.get(
        "/api/v1/archivio/documenti/file",
        params={"percorso": "relazione.txt"},
        headers={"Range": "bytes=4-"},
    )
    elenco = (await admin.get("/api/v1/trasferimenti")).json()
    assert elenco[0]["is_resumed"] is True


async def test_il_registro_e_riservato_agli_amministratori(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/trasferimenti")).status_code == 401


# --- indirizzo del client --------------------------------------------------


# Sotto ASGI la richiesta risulta provenire da 127.0.0.1, che è anche il
# proxy fidato predefinito: i test qui sotto giocano su quello.
_LOCALE = "127.0.0.1"


async def test_x_forwarded_for_ignorato_se_il_mittente_non_e_fidato(
    admin: AsyncClient, share_id: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Quell'intestazione la può scrivere chiunque: fidarsene sempre permetterebbe
    a ogni visitatore di dichiarare l'IP che preferisce."""
    monkeypatch.setattr(get_settings(), "trusted_proxies", "10.9.9.9")

    await admin.get(
        "/api/v1/archivio/documenti/file",
        params={"percorso": "relazione.txt"},
        headers={"X-Forwarded-For": "203.0.113.9"},
    )
    elenco = (await admin.get("/api/v1/trasferimenti")).json()
    assert elenco[0]["client_ip"] == _LOCALE


async def test_x_forwarded_for_letto_dai_proxy_fidati(admin: AsyncClient, share_id: int) -> None:
    await admin.get(
        "/api/v1/archivio/documenti/file",
        params={"percorso": "relazione.txt"},
        headers={"X-Forwarded-For": "203.0.113.9, 10.0.0.1"},
    )
    elenco = (await admin.get("/api/v1/trasferimenti")).json()
    # Il primo della catena è il client originale; gli altri sono i proxy.
    assert elenco[0]["client_ip"] == "203.0.113.9"


async def test_un_forwarded_for_malformato_non_inquina_il_registro(
    admin: AsyncClient, share_id: int
) -> None:
    await admin.get(
        "/api/v1/archivio/documenti/file",
        params={"percorso": "relazione.txt"},
        headers={"X-Forwarded-For": "non-un-indirizzo"},
    )
    elenco = (await admin.get("/api/v1/trasferimenti")).json()
    assert elenco[0]["client_ip"] == _LOCALE


# --- lettura dell'access log -----------------------------------------------


def test_riconosce_una_consegna_nel_log() -> None:
    riga = (
        "203.0.113.9 - - [30/Aug/2026:01:00:00 +0200] "
        '"GET /api/v1/archivio/documenti/file?percorso=foto%2Fmare.jpg&g=xyz HTTP/1.1" '
        '200 240000 "-" "curl/8"'
    )
    esito = accesslog.analizza(riga)
    assert esito is not None
    assert esito.ip == "203.0.113.9"
    assert esito.percorso == "foto/mare.jpg"
    assert esito.byte == 240000
    assert esito.esito is StatoTrasferimento.COMPLETATO


def test_una_ripresa_conta_come_riuscita() -> None:
    """206 è la ripresa di un download interrotto: contarla come fallimento
    farebbe sembrare rotto un sistema che sta funzionando come deve."""
    riga = (
        "10.0.0.5 - - [30/Aug/2026:01:00:00 +0200] "
        '"GET /api/v1/archivio/x/file?percorso=a.bin HTTP/1.1" 206 100'
    )
    esito = accesslog.analizza(riga)
    assert esito is not None
    assert esito.esito is StatoTrasferimento.COMPLETATO


@pytest.mark.parametrize(
    "riga",
    [
        '10.0.0.5 - - [x] "GET /pannello/index.html HTTP/1.1" 200 500',
        '10.0.0.5 - - [x] "POST /api/v1/archivio/x/file?percorso=a HTTP/1.1" 200 5',
        "riga che non e un log",
    ],
)
def test_le_righe_non_pertinenti_vengono_ignorate(riga: str) -> None:
    assert accesslog.analizza(riga) is None


async def test_il_log_chiude_il_trasferimento_con_i_byte_veri(
    admin: AsyncClient, share_id: int
) -> None:
    await admin.get("/api/v1/archivio/documenti/file", params={"percorso": "relazione.txt"})

    from app.core.database import SessionLocal
    from app.services import trasferimenti

    async with SessionLocal() as sessione:
        chiuso = await trasferimenti.concludi(
            sessione,
            "relazione.txt",
            client_ip=_LOCALE,
            byte=11,
            stato=StatoTrasferimento.COMPLETATO,
        )

    assert chiuso is not None
    assert chiuso.bytes_transferred == 11

    elenco = (await admin.get("/api/v1/trasferimenti")).json()
    assert elenco[0]["status"] == "completato"
    assert elenco[0]["bytes_transferred"] == 11
