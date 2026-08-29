"""Test degli endpoint di pubblicazione sul web server.

L'agent è finto: qui interessa che l'API gli mandi valori corretti, che
conservi ciò che è stato scritto davvero, e che un rifiuto del test di
sintassi arrivi all'utente con dentro il motivo.
"""

from typing import Any

import pytest
from app.services import agent_client
from httpx import AsyncClient


class AgentFinto:
    """Registra le richieste ricevute, così i test possono guardarle."""

    def __init__(self) -> None:
        self.richieste: list[tuple[str, dict[str, Any]]] = []
        self.rifiuta: str | None = None

    async def chiedi(
        self, verbo: str, dati: dict[str, Any] | None = None, *, timeout: float = 0
    ) -> dict[str, Any]:
        self.richieste.append((verbo, dati or {}))

        if self.rifiuta is not None and verbo == "vhost.write":
            raise agent_client.AgentRifiuta("comando_fallito", self.rifiuta)

        match verbo:
            case "webserver.detect":
                return {"installati": ["apache", "lighttpd"]}
            case "vhost.preview" | "vhost.write":
                return {"configurazione": "# finta\n<VirtualHost *:80>\n</VirtualHost>\n"}
            case _:
                return {}


@pytest.fixture
def agente(monkeypatch: pytest.MonkeyPatch) -> AgentFinto:
    finto = AgentFinto()
    monkeypatch.setattr(agent_client, "chiedi", finto.chiedi)
    return finto


@pytest.fixture(autouse=True)
async def database_pulito():  # noqa: ANN201
    yield
    from app.core.database import SessionLocal
    from app.models import VHost
    from sqlalchemy import delete

    async with SessionLocal() as sessione:
        await sessione.execute(delete(VHost))
        await sessione.commit()


_VHOST = {"hostname": "archivio.esempio.it", "webserver": "apache", "prefisso": "/"}


async def test_elenca_solo_i_web_server_conosciuti(admin: AsyncClient, agente: AgentFinto) -> None:
    """Un nome che l'API non conosce viene scartato, non fatto esplodere in validazione."""
    risposta = await admin.get("/api/v1/vhosts/disponibili")
    assert risposta.status_code == 200
    assert risposta.json()["installati"] == ["apache"]


async def test_lanteprima_non_scrive_nulla(admin: AsyncClient, agente: AgentFinto) -> None:
    risposta = await admin.post("/api/v1/vhosts/anteprima", json=_VHOST)
    assert risposta.status_code == 200
    assert "VirtualHost" in risposta.json()["configurazione"]
    assert [v for v, _ in agente.richieste] == ["vhost.preview"]


async def test_la_radice_dei_mount_non_viene_mandata_allagent(
    admin: AsyncClient, agente: AgentFinto
) -> None:
    """La conosce l'agent: accettarla dall'API permetterebbe di servire qualunque cartella."""
    await admin.post("/api/v1/vhosts/anteprima", json=_VHOST)
    _, dati = agente.richieste[0]
    assert "radice_mount" not in dati
    assert "mount_root" not in dati


async def test_creazione_conserva_la_configurazione_scritta(
    admin: AsyncClient, agente: AgentFinto
) -> None:
    risposta = await admin.post("/api/v1/vhosts", json=_VHOST)
    assert risposta.status_code == 201

    scritta = await admin.get(f"/api/v1/vhosts/{risposta.json()['id']}/configurazione")
    assert "VirtualHost" in scritta.json()["configurazione"]


async def test_lo_stesso_host_non_si_configura_due_volte(
    admin: AsyncClient, agente: AgentFinto
) -> None:
    await admin.post("/api/v1/vhosts", json=_VHOST)
    secondo = await admin.post("/api/v1/vhosts", json=_VHOST)
    assert secondo.status_code == 409


async def test_il_motivo_del_rifiuto_arriva_allutente(
    admin: AsyncClient, agente: AgentFinto
) -> None:
    """Senza il testo del test di sintassi bisognerebbe leggere i log per capire."""
    agente.rifiuta = "La configurazione non e valida ed e stata annullata. Syntax error on line 7"

    risposta = await admin.post("/api/v1/vhosts", json=_VHOST)
    assert risposta.status_code == 502
    assert "Syntax error on line 7" in risposta.json()["detail"]

    # E non resta nulla nel pannello: il vhost non è stato scritto.
    assert (await admin.get("/api/v1/vhosts")).json() == []


async def test_un_hostname_malformato_non_arriva_nemmeno_allagent(
    admin: AsyncClient, agente: AgentFinto
) -> None:
    risposta = await admin.post(
        "/api/v1/vhosts", json={**_VHOST, "hostname": "", "webserver": "apache"}
    )
    assert risposta.status_code == 422
    assert agente.richieste == []


async def test_eliminare_toglie_prima_il_file_poi_la_riga(
    admin: AsyncClient, agente: AgentFinto
) -> None:
    creato = await admin.post("/api/v1/vhosts", json=_VHOST)
    risposta = await admin.delete(f"/api/v1/vhosts/{creato.json()['id']}")

    assert risposta.status_code == 204
    assert ("vhost.remove", {"webserver": "apache", "hostname": "archivio.esempio.it"}) in [
        (v, d) for v, d in agente.richieste
    ]
    assert (await admin.get("/api/v1/vhosts")).json() == []


async def test_serve_essere_amministratori(client: AsyncClient, agente: AgentFinto) -> None:
    assert (await client.get("/api/v1/vhosts")).status_code == 401
