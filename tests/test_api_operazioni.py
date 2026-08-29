"""Test delle operazioni che modificano il contenuto delle cartelle.

Sono le uniche chiamate che scrivono sul NAS: qui interessa soprattutto che
NON facciano cose che non devono — sovrascrivere in silenzio, svuotare una
cartella su cui non si ha alcun diritto, uscire dalla pubblicazione.
"""

from pathlib import Path
from typing import Any

import pytest
from app.services import agent_client
from httpx import AsyncClient


@pytest.fixture
def cartella(tmp_path: Path) -> Path:
    (tmp_path / "relazione.txt").write_text("testo", encoding="utf-8")
    (tmp_path / "foto").mkdir()
    (tmp_path / "foto" / "mare.txt").write_text("una foto", encoding="utf-8")
    (tmp_path / "vuota").mkdir()
    (tmp_path / "riservata").mkdir()
    (tmp_path / "riservata" / "conti.txt").write_text("riservato", encoding="utf-8")
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
    from app.models import Mount, PermessoUtente, Share, User
    from sqlalchemy import delete

    async with SessionLocal() as sessione:
        await sessione.execute(delete(PermessoUtente))
        await sessione.execute(delete(Share))
        await sessione.execute(delete(Mount))
        # L'amministratore iniziale resta: lo ricrea il lifespan a ogni avvio.
        await sessione.execute(delete(User).where(User.is_admin.is_(False)))
        await sessione.commit()


@pytest.fixture
async def share_id(admin: AsyncClient) -> int:
    risposta = await admin.post(
        "/api/v1/mounts",
        json={
            "slug": "nas-op",
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


async def _utente_semplice(username: str, password: str) -> int:
    """Crea un utente non amministratore, senza passare da un endpoint."""
    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.models import User

    async with SessionLocal() as sessione:
        utente = User(
            username=username,
            password_hash=hash_password(password),
            is_admin=False,
            is_active=True,
        )
        sessione.add(utente)
        await sessione.commit()
        await sessione.refresh(utente)
        return int(utente.id)


# --- creazione e rinomina --------------------------------------------------


async def test_crea_una_cartella(admin: AsyncClient, share_id: int, cartella: Path) -> None:
    risposta = await admin.post(
        "/api/v1/archivio/documenti/cartella", json={"percorso": "", "nome": "contratti"}
    )
    assert risposta.status_code == 201
    assert (cartella / "contratti").is_dir()


async def test_non_sovrascrive_una_cartella_esistente(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.post(
        "/api/v1/archivio/documenti/cartella", json={"percorso": "", "nome": "foto"}
    )
    assert risposta.status_code == 409
    assert "esiste" in risposta.json()["detail"]


@pytest.mark.parametrize(
    "nome",
    [
        "../fuori",
        "con/barra",
        ".nascosto",
        "finisce.",
        "con:duepunti",
        "CON",
        "  ",
    ],
)
async def test_nomi_inutilizzabili_rifiutati(admin: AsyncClient, share_id: int, nome: str) -> None:
    """Nomi che il NAS accetterebbe ma che poi risultano inapribili da SMB o Windows."""
    risposta = await admin.post(
        "/api/v1/archivio/documenti/cartella", json={"percorso": "", "nome": nome}
    )
    assert risposta.status_code in (409, 422)


async def test_rinomina_un_file(admin: AsyncClient, share_id: int, cartella: Path) -> None:
    risposta = await admin.post(
        "/api/v1/archivio/documenti/rinomina",
        json={"percorso": "relazione.txt", "nome": "relazione-2026.txt"},
    )
    assert risposta.status_code == 200
    assert risposta.json()["percorso"] == "relazione-2026.txt"
    assert not (cartella / "relazione.txt").exists()
    assert (cartella / "relazione-2026.txt").read_text(encoding="utf-8") == "testo"


# --- spostamento e copia ---------------------------------------------------


async def test_sposta_un_file_in_unaltra_cartella(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    risposta = await admin.post(
        "/api/v1/archivio/documenti/sposta",
        json={"percorso": "relazione.txt", "destinazione": "foto"},
    )
    assert risposta.status_code == 200
    assert (cartella / "foto" / "relazione.txt").exists()
    assert not (cartella / "relazione.txt").exists()


async def test_una_cartella_non_si_sposta_dentro_se_stessa(
    admin: AsyncClient, share_id: int
) -> None:
    risposta = await admin.post(
        "/api/v1/archivio/documenti/sposta",
        json={"percorso": "foto", "destinazione": "foto"},
    )
    assert risposta.status_code == 409


async def test_copia_una_cartella_con_il_suo_contenuto(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    risposta = await admin.post(
        "/api/v1/archivio/documenti/copia",
        json={"percorso": "foto", "destinazione": "", "nome": "foto-copia"},
    )
    assert risposta.status_code == 200
    assert (cartella / "foto-copia" / "mare.txt").exists()
    # L'originale resta dov'era.
    assert (cartella / "foto" / "mare.txt").exists()


# --- eliminazione ----------------------------------------------------------


async def test_elimina_un_file(admin: AsyncClient, share_id: int, cartella: Path) -> None:
    risposta = await admin.post(
        "/api/v1/archivio/documenti/elimina", json={"percorso": "relazione.txt"}
    )
    assert risposta.status_code == 204
    assert not (cartella / "relazione.txt").exists()


async def test_una_cartella_piena_non_si_elimina_per_sbaglio(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    """Chi crede di cancellare una cartella vuota non deve perderne il contenuto."""
    risposta = await admin.post("/api/v1/archivio/documenti/elimina", json={"percorso": "foto"})
    assert risposta.status_code == 409
    assert (cartella / "foto" / "mare.txt").exists()

    confermato = await admin.post(
        "/api/v1/archivio/documenti/elimina", json={"percorso": "foto", "ricorsivo": True}
    )
    assert confermato.status_code == 204
    assert not (cartella / "foto").exists()


async def test_una_cartella_vuota_si_elimina_senza_conferma(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    risposta = await admin.post("/api/v1/archivio/documenti/elimina", json={"percorso": "vuota"})
    assert risposta.status_code == 204
    assert not (cartella / "vuota").exists()


async def test_la_radice_della_pubblicazione_non_si_elimina(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    risposta = await admin.post("/api/v1/archivio/documenti/elimina", json={"percorso": "/"})
    assert risposta.status_code == 400
    assert cartella.is_dir()


# --- permessi --------------------------------------------------------------


async def test_chi_puo_leggere_non_puo_modificare(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    """La cartella è pubblica, quindi un anonimo la legge — ma non deve poterla cambiare."""
    lettura = await _anonimo(admin).get("/api/v1/archivio/documenti")
    assert lettura.status_code == 200

    risposta = await _anonimo(admin).post(
        "/api/v1/archivio/documenti/elimina", json={"percorso": "relazione.txt"}
    )
    assert risposta.status_code == 403
    assert (cartella / "relazione.txt").exists()


async def test_spostare_richiede_il_permesso_anche_sullorigine(
    admin: AsyncClient, share_id: int, cartella: Path
) -> None:
    """Chiederlo solo sulla destinazione permetterebbe di svuotare cartelle altrui."""
    # L'utente si crea direttamente nel database: la sua gestione
    # dall'interfaccia non c'è ancora, ma la regola da verificare sì.
    utente_id = await _utente_semplice("mario", "password-lunga")

    await admin.put(
        f"/api/v1/shares/{share_id}/permessi",
        json={"user_id": utente_id, "path_prefix": "foto", "livello": "scrittura"},
    )
    accesso = await admin.post(
        "/api/v1/auth/login", json={"username": "mario", "password": "password-lunga"}
    )
    admin.headers["Authorization"] = f"Bearer {accesso.json()['access_token']}"

    # Mario può scrivere in "foto", ma non nella radice da cui vorrebbe togliere.
    risposta = await admin.post(
        "/api/v1/archivio/documenti/sposta",
        json={"percorso": "relazione.txt", "destinazione": "foto"},
    )
    assert risposta.status_code == 403
    assert (cartella / "relazione.txt").exists()


async def test_risalite_rifiutate(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.post(
        "/api/v1/archivio/documenti/cartella",
        json={"percorso": "../../etc", "nome": "prova"},
    )
    assert risposta.status_code == 400
