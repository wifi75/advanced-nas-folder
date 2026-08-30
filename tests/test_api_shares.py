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


# --- cambio del nome nell'indirizzo ----------------------------------------


async def test_il_nome_nellindirizzo_si_puo_cambiare(admin: AsyncClient, share_id: int) -> None:
    """Chi pubblica deve poter scegliere l'indirizzo, anche dopo."""
    risposta = await admin.patch(f"/api/v1/shares/{share_id}", json={"slug": "ricette"})

    assert risposta.status_code == 200
    assert risposta.json()["slug"] == "ricette"


async def test_il_vecchio_indirizzo_smette_di_rispondere(admin: AsyncClient, share_id: int) -> None:
    """E' la conseguenza del cambio, e il pannello la annuncia prima: qui si
    verifica che accada davvero, invece di restare due indirizzi validi."""
    vecchio = (await admin.get(f"/api/v1/shares/{share_id}")).json()["slug"]
    await admin.patch(f"/api/v1/shares/{share_id}", json={"slug": "ricette"})

    assert (await admin.get(f"/api/v1/archivio/{vecchio}")).status_code == 404


async def test_non_si_puo_prendere_un_nome_gia_usato(admin: AsyncClient, share_id: int) -> None:
    altra = await admin.post(
        "/api/v1/shares",
        json={
            "slug": "occupato",
            "label": "Occupato",
            "mount_id": (await admin.get(f"/api/v1/shares/{share_id}")).json()["mount_id"],
            "default_visibility": "utenti",
        },
    )
    assert altra.status_code == 201

    risposta = await admin.patch(f"/api/v1/shares/{share_id}", json={"slug": "occupato"})

    assert risposta.status_code == 409


async def test_un_nome_non_adatto_a_un_indirizzo_viene_rifiutato(
    admin: AsyncClient, share_id: int
) -> None:
    assert (
        await admin.patch(f"/api/v1/shares/{share_id}", json={"slug": "con spazio"})
    ).status_code == 422


# --- cambio dell'origine ----------------------------------------------------


async def test_la_sottocartella_si_puo_cambiare(admin: AsyncClient, share_id: int) -> None:
    """Correggere un percorso sbagliato non deve costringere a rifare tutto:
    permessi, regole e link della pubblicazione restano dove sono."""
    risposta = await admin.patch(f"/api/v1/shares/{share_id}", json={"subpath": "Ricette/Dolci"})

    assert risposta.status_code == 200
    assert (await admin.get(f"/api/v1/shares/{share_id}")).json()["subpath"] == "Ricette/Dolci"


async def test_la_sottocartella_si_puo_svuotare(admin: AsyncClient, share_id: int) -> None:
    """Vuoto significa «pubblica la radice della condivisione»."""
    await admin.patch(f"/api/v1/shares/{share_id}", json={"subpath": "Ricette"})
    await admin.patch(f"/api/v1/shares/{share_id}", json={"subpath": ""})

    assert (await admin.get(f"/api/v1/shares/{share_id}")).json()["subpath"] == ""


async def test_una_risalita_nella_sottocartella_viene_rifiutata(
    admin: AsyncClient, share_id: int
) -> None:
    """Senza questo si pubblicherebbe una cartella fuori dal mount."""
    risposta = await admin.patch(f"/api/v1/shares/{share_id}", json={"subpath": "../../etc"})

    assert risposta.status_code in (400, 422)


async def test_non_si_puo_puntare_a_una_condivisione_inesistente(
    admin: AsyncClient, share_id: int
) -> None:
    risposta = await admin.patch(f"/api/v1/shares/{share_id}", json={"mount_id": 9999})

    assert risposta.status_code == 400


# --- nomi da nascondere -----------------------------------------------------


async def test_le_cartelle_di_servizio_del_nas_sono_nascoste_da_subito(
    admin: AsyncClient, share_id: int
) -> None:
    """Il cestino di un Synology non e' contenuto da pubblicare, e chi riceve
    l'indirizzo non deve nemmeno vederlo. Proposto, non imposto: si toglie."""
    elenco = (await admin.get(f"/api/v1/shares/{share_id}")).json()

    assert "#recycle" in elenco["hidden_patterns"]
    assert "@eaDir" in elenco["hidden_patterns"]


async def test_lelenco_dei_nomi_nascosti_si_puo_cambiare(admin: AsyncClient, share_id: int) -> None:
    risposta = await admin.patch(f"/api/v1/shares/{share_id}", json={"hidden_patterns": "vecchi"})

    assert risposta.status_code == 200
    assert (await admin.get(f"/api/v1/shares/{share_id}")).json()["hidden_patterns"] == "vecchi"


async def test_si_puo_svuotare_per_mostrare_tutto(admin: AsyncClient, share_id: int) -> None:
    await admin.patch(f"/api/v1/shares/{share_id}", json={"hidden_patterns": ""})

    assert (await admin.get(f"/api/v1/shares/{share_id}")).json()["hidden_patterns"] == ""
