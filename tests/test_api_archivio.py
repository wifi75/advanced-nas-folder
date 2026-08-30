"""Test della consultazione e del download delle cartelle pubblicate.

Questi test lavorano su una cartella vera del disco: e' l'unico modo di
verificare che il filtro per voce, la risoluzione dei percorsi e la consegna
del file combacino davvero.
"""

from pathlib import Path
from typing import Any

import pytest
from app.core.config import get_settings
from app.services import agent_client
from httpx import AsyncClient


@pytest.fixture
def cartella(tmp_path: Path) -> Path:
    """Una pubblicazione finta con dentro qualcosa da elencare."""
    (tmp_path / "pubblico.txt").write_text("visibile a tutti", encoding="utf-8")
    (tmp_path / ".nascosto").write_text("non deve comparire", encoding="utf-8")
    (tmp_path / "contabilita").mkdir()
    (tmp_path / "contabilita" / "bilancio.txt").write_text("riservato", encoding="utf-8")
    (tmp_path / "foto").mkdir()
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
    """Nei test il file lo invia l'applicazione: qui non c'e' un web server."""
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
            "slug": "nas-prova",
            "label": "NAS di prova",
            "server": "192.168.1.10",
            "export_path": "/volume1/dati",
        },
    )
    mount_id = risposta.json()["id"]
    risposta = await admin.post(
        "/api/v1/shares",
        json={
            "slug": "documenti",
            "label": "Documenti",
            "mount_id": mount_id,
            "default_visibility": "pubblica",
        },
    )
    return int(risposta.json()["id"])


def _anonimo(client: AsyncClient) -> AsyncClient:
    """Lo stesso client senza il token: simula un visitatore qualunque."""
    client.headers.pop("Authorization", None)
    return client


# --- consultazione ---------------------------------------------------------


async def test_cartella_pubblica_visibile_senza_accedere(admin: AsyncClient, share_id: int) -> None:
    risposta = await _anonimo(admin).get("/api/v1/archivio/documenti")
    assert risposta.status_code == 200

    nomi = [v["nome"] for v in risposta.json()["voci"]]
    assert "pubblico.txt" in nomi
    # Le cartelle vengono prima dei file.
    assert nomi.index("contabilita") < nomi.index("pubblico.txt")


async def test_i_file_nascosti_non_compaiono(admin: AsyncClient, share_id: int) -> None:
    risposta = await _anonimo(admin).get("/api/v1/archivio/documenti")
    assert ".nascosto" not in [v["nome"] for v in risposta.json()["voci"]]


async def test_una_sottocartella_negata_sparisce_dallelenco(
    admin: AsyncClient, share_id: int
) -> None:
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "contabilita", "visibility": "negata"},
    )
    risposta = await _anonimo(admin).get("/api/v1/archivio/documenti")
    nomi = [v["nome"] for v in risposta.json()["voci"]]
    assert "contabilita" not in nomi
    assert "pubblico.txt" in nomi


async def test_una_sottocartella_riservata_non_si_apre(admin: AsyncClient, share_id: int) -> None:
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "contabilita", "visibility": "utenti"},
    )
    risposta = await _anonimo(admin).get(
        "/api/v1/archivio/documenti", params={"percorso": "contabilita"}
    )
    assert risposta.status_code == 403


async def test_pubblicazione_disattivata_non_esiste_per_chi_guarda(
    admin: AsyncClient, share_id: int
) -> None:
    await admin.patch(f"/api/v1/shares/{share_id}", json={"is_enabled": False})
    risposta = await _anonimo(admin).get("/api/v1/archivio/documenti")
    assert risposta.status_code == 404


async def test_le_briciole_ricostruiscono_il_percorso(admin: AsyncClient, share_id: int) -> None:
    risposta = await _anonimo(admin).get(
        "/api/v1/archivio/documenti", params={"percorso": "contabilita"}
    )
    assert risposta.json()["briciole"] == [["contabilita", "contabilita"]]


async def test_risalita_rifiutata_con_errore_comprensibile(
    admin: AsyncClient, share_id: int
) -> None:
    risposta = await _anonimo(admin).get(
        "/api/v1/archivio/documenti", params={"percorso": "../../etc"}
    )
    assert risposta.status_code == 400


# --- download --------------------------------------------------------------


async def test_download_di_un_file_pubblico(admin: AsyncClient, share_id: int) -> None:
    risposta = await _anonimo(admin).get(
        "/api/v1/archivio/documenti/file", params={"percorso": "pubblico.txt"}
    )
    assert risposta.status_code == 200
    assert risposta.text == "visibile a tutti"
    assert "attachment" in risposta.headers["content-disposition"]


async def test_download_negato_dove_lelenco_e_negato(admin: AsyncClient, share_id: int) -> None:
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "contabilita", "visibility": "negata"},
    )
    risposta = await _anonimo(admin).get(
        "/api/v1/archivio/documenti/file",
        params={"percorso": "contabilita/bilancio.txt"},
    )
    assert risposta.status_code == 403


async def test_una_cartella_non_si_scarica_come_file(admin: AsyncClient, share_id: int) -> None:
    risposta = await _anonimo(admin).get(
        "/api/v1/archivio/documenti/file", params={"percorso": "contabilita"}
    )
    assert risposta.status_code == 404


async def test_il_gettone_apre_solo_il_percorso_per_cui_e_stato_emesso(
    admin: AsyncClient, share_id: int
) -> None:
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "contabilita", "visibility": "utenti"},
    )
    risposta = await admin.post(
        "/api/v1/archivio/documenti/gettone",
        json={"percorso": "contabilita/bilancio.txt"},
    )
    gettone = risposta.json()["gettone"]

    anonimo = _anonimo(admin)
    consentito = await anonimo.get(
        "/api/v1/archivio/documenti/file",
        params={"percorso": "contabilita/bilancio.txt", "g": gettone},
    )
    assert consentito.status_code == 200
    assert consentito.text == "riservato"

    # Lo stesso gettone su un altro percorso non vale: se valesse, un solo
    # collegamento aprirebbe tutta la pubblicazione.
    altrove = await anonimo.get(
        "/api/v1/archivio/documenti/file",
        params={"percorso": "contabilita", "g": gettone},
    )
    assert altrove.status_code == 403


async def test_gettone_manomesso_rifiutato(admin: AsyncClient, share_id: int) -> None:
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "contabilita", "visibility": "utenti"},
    )
    risposta = await _anonimo(admin).get(
        "/api/v1/archivio/documenti/file",
        params={"percorso": "contabilita/bilancio.txt", "g": "non-e-un-gettone"},
    )
    assert risposta.status_code == 403


# --- cosa serve per entrare -------------------------------------------------


async def test_una_cartella_a_password_lo_dice(admin: AsyncClient, anonimo, share_id: int) -> None:  # noqa: ANN001
    """Un 403 uguale in tutti i casi obbliga il pannello a indovinare, e chi
    arrivava si vedeva chiedere una parola d'ordine anche dove serviva un
    account."""
    await admin.patch(f"/api/v1/shares/{share_id}", json={"default_visibility": "password"})
    await admin.post(
        f"/api/v1/shares/{share_id}/regole",
        json={"path_prefix": "", "visibility": "password", "password": "segreto"},
    )

    risposta = await anonimo("/api/v1/archivio/documenti")

    assert risposta.status_code == 403
    assert risposta.headers.get("X-Anf-Richiede") == "password"


async def test_una_cartella_per_utenti_chiede_di_accedere(
    admin: AsyncClient, anonimo, share_id: int
) -> None:  # noqa: ANN001
    await admin.patch(f"/api/v1/shares/{share_id}", json={"default_visibility": "utenti"})

    risposta = await anonimo("/api/v1/archivio/documenti")

    assert risposta.status_code in (401, 403)
    if risposta.status_code == 403:
        assert risposta.headers.get("X-Anf-Richiede") == "accesso"


async def test_a_chi_e_gia_dentro_non_si_chiede_altro(admin: AsyncClient, share_id: int) -> None:
    """Autenticato e comunque respinto: nessuna credenziale cambierebbe
    l'esito, e proporre un accesso sarebbe un giro a vuoto."""
    await admin.patch(f"/api/v1/shares/{share_id}", json={"default_visibility": "negata"})

    risposta = await admin.get("/api/v1/archivio/documenti")

    assert risposta.status_code == 403
    assert risposta.headers.get("X-Anf-Richiede") == "niente"
