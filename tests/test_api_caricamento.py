"""Test del caricamento a blocchi.

Il comportamento che conta non è «il file arriva», ma cosa succede quando
*non* arriva tutto: un caricamento interrotto deve poter riprendere, e uno
incompleto non deve mai finire fra i file buoni.
"""

from pathlib import Path
from typing import Any

import pytest
from app.services import agent_client
from httpx import AsyncClient


@pytest.fixture
def cartella(tmp_path: Path) -> Path:
    (tmp_path / "esistente.txt").write_text("gia qui", encoding="utf-8")
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
            "slug": "nas-up",
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


_CARICA = "/api/v1/archivio/documenti/carica"


async def _blocco(client: AsyncClient, nome: str, dati: bytes, offset: int) -> Any:  # noqa: ANN401 - è la risposta httpx
    return await client.put(
        _CARICA, params={"nome": nome, "offset": offset, "percorso": ""}, content=dati
    )


# --- caricamento normale ---------------------------------------------------


async def test_un_file_arriva_a_blocchi(admin: AsyncClient, share_id: int, cartella: Path) -> None:
    assert (await _blocco(admin, "nuovo.txt", b"prima parte ", 0)).json()["ricevuti"] == 12
    assert (await _blocco(admin, "nuovo.txt", b"seconda parte", 12)).json()["ricevuti"] == 25

    fine = await admin.post(
        f"{_CARICA}/completa", json={"percorso": "", "nome": "nuovo.txt", "dimensione": 25}
    )
    assert fine.status_code == 201
    assert (cartella / "nuovo.txt").read_text(encoding="utf-8") == "prima parte seconda parte"


async def test_il_file_a_meta_non_compare_fra_i_file(admin: AsyncClient, share_id: int) -> None:
    """Un caricamento in corso non deve sembrare un file scaricabile."""
    await _blocco(admin, "grande.bin", b"solo l'inizio", 0)

    elenco = await admin.get("/api/v1/archivio/documenti")
    assert [v["nome"] for v in elenco.json()["voci"]] == ["esistente.txt"]


# --- ripresa ---------------------------------------------------------------


async def test_lo_stato_dice_da_dove_riprendere(admin: AsyncClient, share_id: int) -> None:
    await _blocco(admin, "interrotto.bin", b"1234567890", 0)

    stato = await admin.get(f"{_CARICA}/stato", params={"nome": "interrotto.bin", "percorso": ""})
    assert stato.json() == {"nome": "interrotto.bin", "ricevuti": 10, "gia_presente": False}


async def test_un_caricamento_mai_iniziato_riparte_da_zero(
    admin: AsyncClient, share_id: int
) -> None:
    stato = await admin.get(f"{_CARICA}/stato", params={"nome": "mai-visto.bin", "percorso": ""})
    assert stato.json()["ricevuti"] == 0


async def test_lo_stato_avverte_se_il_file_esiste_gia(admin: AsyncClient, share_id: int) -> None:
    stato = await admin.get(f"{_CARICA}/stato", params={"nome": "esistente.txt", "percorso": ""})
    assert stato.json()["gia_presente"] is True


async def test_un_blocco_alla_posizione_sbagliata_viene_rifiutato(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    """Scrivere comunque produrrebbe un file corrotto che nessuno nota fino all'apertura."""
    await _blocco(admin, "attento.bin", b"1234567890", 0)

    risposta = await _blocco(admin, "attento.bin", b"fuori posto", 99)
    assert risposta.status_code == 409
    assert "riparte dal byte 10" in risposta.json()["detail"]


# --- completamento ---------------------------------------------------------


async def test_un_file_incompleto_non_si_completa(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    """Meglio poterlo riprendere che ritrovarselo troncato fra i file buoni."""
    await _blocco(admin, "troncato.bin", b"met", 0)

    risposta = await admin.post(
        f"{_CARICA}/completa", json={"percorso": "", "nome": "troncato.bin", "dimensione": 100}
    )
    assert risposta.status_code == 409
    assert not (cartella / "troncato.bin").exists()

    # Il parziale resta: il caricamento si può ancora riprendere.
    stato = await admin.get(f"{_CARICA}/stato", params={"nome": "troncato.bin", "percorso": ""})
    assert stato.json()["ricevuti"] == 3


async def test_non_si_sovrascrive_un_file_esistente(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    await _blocco(admin, "esistente.txt", b"nuovo contenuto", 0)

    risposta = await admin.post(
        f"{_CARICA}/completa", json={"percorso": "", "nome": "esistente.txt"}
    )
    assert risposta.status_code == 409
    assert (cartella / "esistente.txt").read_text(encoding="utf-8") == "gia qui"


async def test_completare_senza_aver_caricato_nulla(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.post(f"{_CARICA}/completa", json={"percorso": "", "nome": "vuoto.bin"})
    assert risposta.status_code == 409


# --- annullamento e permessi -----------------------------------------------


async def test_annullare_toglie_il_file_parziale(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    await _blocco(admin, "ripensamento.bin", b"qualcosa", 0)
    assert list(cartella.glob(".*anf-parziale"))

    risposta = await admin.post(
        f"{_CARICA}/annulla", json={"percorso": "", "nome": "ripensamento.bin"}
    )
    assert risposta.status_code == 204
    assert not list(cartella.glob(".*anf-parziale"))


async def test_chi_non_puo_scrivere_non_puo_caricare(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    admin.headers.pop("Authorization", None)

    risposta = await _blocco(admin, "abusivo.bin", b"dati", 0)
    assert risposta.status_code == 403
    assert not list(cartella.glob(".*anf-parziale"))


async def test_un_blocco_vuoto_viene_rifiutato(admin: AsyncClient, share_id: int) -> None:
    risposta = await _blocco(admin, "niente.bin", b"", 0)
    assert risposta.status_code == 400


async def test_nome_inutilizzabile_rifiutato(admin: AsyncClient, share_id: int) -> None:
    risposta = await _blocco(admin, "../fuori.bin", b"dati", 0)
    assert risposta.status_code == 409
