"""Test degli endpoint dei mount.

L'agent non viene eseguito: al suo posto una finta risposta. Qui si verifica
che l'API si comporti bene, non che l'agent funzioni — quello ha i suoi test e
viene provato contro un NAS reale.
"""

from typing import Any

import pytest
from app.services import agent_client
from httpx import AsyncClient


class AgentFinto:
    """Registra le richieste ricevute e risponde con cio che gli si dice."""

    def __init__(self) -> None:
        self.richieste: list[tuple[str, dict[str, Any]]] = []
        self.risposte: dict[str, Any] = {}
        self.solleva: Exception | None = None

    async def chiedi(
        self, verbo: str, dati: dict[str, Any] | None = None, *, timeout: float = 0
    ) -> dict[str, Any]:
        dati = dati or {}
        self.richieste.append((verbo, dati))
        if self.solleva is not None:
            raise self.solleva
        if verbo == "mount.create":
            # Come l'agent vero: il percorso si ricava dallo slug, non e un
            # valore fisso. Restituirne uno solo per tutti nasconderebbe il
            # vincolo di unicita che il database applica davvero.
            return {"mountpoint": f"/srv/nas/{dati.get('slug')}"}
        return self.risposte.get(verbo, {})

    def ultima(self, verbo: str) -> dict[str, Any]:
        for v, dati in reversed(self.richieste):
            if v == verbo:
                return dati
        raise AssertionError(f"nessuna richiesta {verbo!r}")


@pytest.fixture
def agente(monkeypatch: pytest.MonkeyPatch) -> AgentFinto:
    finto = AgentFinto()
    finto.risposte["mount.status"] = {"montato": False}
    monkeypatch.setattr(agent_client, "chiedi", finto.chiedi)
    return finto


@pytest.fixture(autouse=True)
async def database_pulito():  # noqa: ANN201
    """Svuota la tabella dei mount dopo ogni test.

    I test condividono lo stesso file di database: senza questo, l'ordine di
    esecuzione cambierebbe l'esito, che e il modo piu insidioso di avere una
    suite inaffidabile.
    """
    yield
    from app.core.database import SessionLocal
    from app.models import Mount
    from sqlalchemy import delete

    async with SessionLocal() as sessione:
        await sessione.execute(delete(Mount))
        await sessione.commit()


CREAZIONE = {
    "slug": "prova",
    "label": "Prova",
    "server": "192.168.1.10",
    "export_path": "/volume1/dati",
}


# --- accesso ---


async def test_serve_autenticazione(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/mounts")).status_code == 401


async def test_creazione_richiede_autenticazione(client: AsyncClient) -> None:
    assert (await client.post("/api/v1/mounts", json=CREAZIONE)).status_code == 401


# --- creazione ---


async def test_crea_mount(admin: AsyncClient, agente: AgentFinto) -> None:
    risposta = await admin.post("/api/v1/mounts", json=CREAZIONE)
    assert risposta.status_code == 201
    corpo = risposta.json()
    assert corpo["slug"] == "prova"
    assert corpo["server"] == "192.168.1.10"


async def test_scrittura_disattivata_per_impostazione_predefinita(
    admin: AsyncClient, agente: AgentFinto
) -> None:
    """La scrittura non deve mai attivarsi per distrazione."""
    risposta = await admin.post("/api/v1/mounts", json={**CREAZIONE, "slug": "sola-lettura"})
    assert risposta.json()["requested_access"] == "ro"
    assert "ro" in agente.ultima("mount.create")["opzioni"]
    assert "rw" not in agente.ultima("mount.create")["opzioni"]


async def test_scrittura_richiesta_esplicitamente(admin: AsyncClient, agente: AgentFinto) -> None:
    risposta = await admin.post(
        "/api/v1/mounts", json={**CREAZIONE, "slug": "scrivibile", "consenti_scrittura": True}
    )
    assert risposta.json()["requested_access"] == "rw"
    assert "rw" in agente.ultima("mount.create")["opzioni"]


async def test_il_percorso_non_e_scelto_dall_utente(admin: AsyncClient, agente: AgentFinto) -> None:
    """Anche passando un mountpoint, viene ignorato: lo impone l'agent."""
    risposta = await admin.post(
        "/api/v1/mounts",
        json={**CREAZIONE, "slug": "imposto", "mountpoint": "/etc/passwd"},
    )
    assert risposta.status_code == 201
    assert "/etc" not in risposta.json()["mountpoint"]


@pytest.mark.parametrize("slug", ["../../etc", "a/b", "MAIUSCOLE", "-iniziale", "con spazio", ""])
async def test_slug_non_validi_respinti(admin: AsyncClient, agente: AgentFinto, slug: str) -> None:
    risposta = await admin.post("/api/v1/mounts", json={**CREAZIONE, "slug": slug})
    assert risposta.status_code == 422


async def test_slug_duplicato(admin: AsyncClient, agente: AgentFinto) -> None:
    await admin.post("/api/v1/mounts", json={**CREAZIONE, "slug": "doppio"})
    risposta = await admin.post("/api/v1/mounts", json={**CREAZIONE, "slug": "doppio"})
    assert risposta.status_code == 409


async def test_versione_nfs_non_valida(admin: AsyncClient, agente: AgentFinto) -> None:
    risposta = await admin.post(
        "/api/v1/mounts", json={**CREAZIONE, "slug": "versione", "nfs_version": "9"}
    )
    assert risposta.status_code == 422


# --- opzioni inviate all'agent ---


async def test_opzioni_di_resilienza_sempre_presenti(
    admin: AsyncClient, agente: AgentFinto
) -> None:
    """Sono le opzioni che evitano che un NAS spento blocchi il server."""
    await admin.post("/api/v1/mounts", json={**CREAZIONE, "slug": "resiliente"})
    opzioni = agente.ultima("mount.create")["opzioni"]
    for attesa in ("nofail", "soft", "nolock", "x-systemd.automount"):
        assert attesa in opzioni


async def test_senza_automount_niente_opzione(admin: AsyncClient, agente: AgentFinto) -> None:
    await admin.post("/api/v1/mounts", json={**CREAZIONE, "slug": "senza-auto", "automount": False})
    assert "x-systemd.automount" not in agente.ultima("mount.create")["opzioni"]


# --- guasti dell'agent ---


async def test_agent_non_disponibile(admin: AsyncClient, agente: AgentFinto) -> None:
    agente.solleva = agent_client.AgentNonDisponibile("agent spento")
    risposta = await admin.post("/api/v1/mounts", json={**CREAZIONE, "slug": "assente"})
    assert risposta.status_code == 503


async def test_rifiuto_per_validazione_e_richiesta_errata(
    admin: AsyncClient, agente: AgentFinto
) -> None:
    agente.solleva = agent_client.AgentRifiuta("validazione", "Opzione non consentita")
    risposta = await admin.post("/api/v1/mounts", json={**CREAZIONE, "slug": "invalido"})
    assert risposta.status_code == 400


async def test_altri_rifiuti_sono_problemi_a_monte(admin: AsyncClient, agente: AgentFinto) -> None:
    agente.solleva = agent_client.AgentRifiuta("comando_fallito", "NAS irraggiungibile")
    risposta = await admin.post("/api/v1/mounts", json={**CREAZIONE, "slug": "guasto"})
    assert risposta.status_code == 502


# --- ciclo di vita ---


async def test_avvia_e_ferma(admin: AsyncClient, agente: AgentFinto) -> None:
    creato = await admin.post("/api/v1/mounts", json={**CREAZIONE, "slug": "ciclo"})
    identificativo = creato.json()["id"]

    agente.risposte["mount.start"] = {
        "montato": True,
        "opzioni": "ro,vers=3",
        "scrittura": False,
        "scrittura_verificata": False,
    }
    avviato = await admin.post(f"/api/v1/mounts/{identificativo}/avvia")
    assert avviato.status_code == 200
    assert avviato.json()["state"] == "montato"

    agente.risposte["mount.stop"] = {"montato": False}
    fermato = await admin.post(f"/api/v1/mounts/{identificativo}/ferma")
    assert fermato.json()["state"] == "smontato"


async def test_avviso_quando_il_nas_nega_la_scrittura(
    admin: AsyncClient, agente: AgentFinto
) -> None:
    """È la condizione che l'utente deve vedere, non scoprire al primo upload."""
    creato = await admin.post(
        "/api/v1/mounts",
        json={**CREAZIONE, "slug": "negata", "consenti_scrittura": True},
    )
    identificativo = creato.json()["id"]

    agente.risposte["mount.start"] = {
        "montato": True,
        "opzioni": "ro,vers=3",
        "scrittura": False,
        "scrittura_verificata": False,
    }
    risposta = await admin.post(f"/api/v1/mounts/{identificativo}/avvia")
    avviso = risposta.json()["avviso"]
    assert avviso is not None
    assert "sola lettura" in avviso


async def test_mount_inesistente(admin: AsyncClient, agente: AgentFinto) -> None:
    assert (await admin.get("/api/v1/mounts/99999")).status_code == 404


async def test_elimina(admin: AsyncClient, agente: AgentFinto) -> None:
    creato = await admin.post("/api/v1/mounts", json={**CREAZIONE, "slug": "da-togliere"})
    identificativo = creato.json()["id"]
    assert (await admin.delete(f"/api/v1/mounts/{identificativo}")).status_code == 204
    assert (await admin.get(f"/api/v1/mounts/{identificativo}")).status_code == 404


async def test_non_elimina_se_agent_non_risponde(admin: AsyncClient, agente: AgentFinto) -> None:
    """Cancellare il record lascerebbe unit systemd orfane sul sistema."""
    creato = await admin.post("/api/v1/mounts", json={**CREAZIONE, "slug": "orfano"})
    identificativo = creato.json()["id"]

    agente.solleva = agent_client.AgentNonDisponibile("agent spento")
    assert (await admin.delete(f"/api/v1/mounts/{identificativo}")).status_code == 503

    agente.solleva = None
    assert (await admin.get(f"/api/v1/mounts/{identificativo}")).status_code == 200


# --- scoperta ---


async def test_scoperta(admin: AsyncClient, agente: AgentFinto) -> None:
    agente.risposte["nfs.discover"] = {
        "server": "192.168.1.10",
        "esportazioni": [{"percorso": "/volume1/dati", "client": "192.168.1.0/24"}],
        "versioni": ["2", "3"],
    }
    risposta = await admin.post("/api/v1/mounts/discover", json={"server": "192.168.1.10"})
    assert risposta.status_code == 200
    corpo = risposta.json()
    assert corpo["esportazioni"][0]["percorso"] == "/volume1/dati"
    assert "4" not in corpo["versioni"]
