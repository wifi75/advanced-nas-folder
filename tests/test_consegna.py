"""Test della consegna dei file al web server."""

from pathlib import Path

import pytest
from app.core.config import get_settings
from app.services import consegna


@pytest.fixture
def radice(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr(get_settings(), "mount_root", tmp_path)
    return tmp_path


def _modo(monkeypatch: pytest.MonkeyPatch, valore: str) -> None:
    monkeypatch.setattr(get_settings(), "download_backend", valore)


def test_apache_riceve_il_percorso_assoluto(monkeypatch: pytest.MonkeyPatch, radice: Path) -> None:
    _modo(monkeypatch, "xsendfile")
    file = radice / "nas" / "relazione.pdf"
    esito = consegna.prepara(file, "relazione.pdf")

    assert esito.intestazioni["X-Sendfile"] == str(file)
    # Il corpo non lo manda l'applicazione: e' tutto il punto della delega.
    assert esito.invia_direttamente is None


def test_nginx_riceve_un_percorso_interno_relativo_alla_radice(
    monkeypatch: pytest.MonkeyPatch, radice: Path
) -> None:
    _modo(monkeypatch, "xaccel")
    esito = consegna.prepara(radice / "nas" / "foto" / "mare.jpg", "mare.jpg")

    # Nginx risolve il prefisso interno sulla radice dei mount: un percorso
    # assoluto qui darebbe un 404 senza spiegazione.
    assert esito.intestazioni["X-Accel-Redirect"] == "/__anf_internal/nas/foto/mare.jpg"


def test_percorso_interno_codificato(monkeypatch: pytest.MonkeyPatch, radice: Path) -> None:
    _modo(monkeypatch, "xaccel")
    esito = consegna.prepara(radice / "documenti vecchi" / "à.txt", "à.txt")

    interno = esito.intestazioni["X-Accel-Redirect"]
    assert " " not in interno
    assert "%20" in interno


def test_in_sviluppo_il_file_lo_manda_lapplicazione(
    monkeypatch: pytest.MonkeyPatch, radice: Path
) -> None:
    _modo(monkeypatch, "stream")
    file = radice / "nota.txt"
    esito = consegna.prepara(file, "nota.txt")

    assert esito.invia_direttamente == file
    assert "X-Sendfile" not in esito.intestazioni


@pytest.mark.parametrize("nome", ["pagina.html", "disegno.svg", "dati.xml"])
def test_i_file_interpretabili_dal_browser_non_conservano_il_tipo(nome: str) -> None:
    """Servirli con il loro tipo reale li farebbe eseguire nel contesto del pannello."""
    assert consegna.tipo_contenuto(nome) == "application/octet-stream"


def test_i_tipi_innocui_restano_quelli_veri() -> None:
    assert consegna.tipo_contenuto("foto.jpg") == "image/jpeg"


def test_il_nome_con_accenti_viaggia_in_due_forme(
    monkeypatch: pytest.MonkeyPatch, radice: Path
) -> None:
    """Senza la forma UTF-8 il nome arriva storpiato; senza quella ASCII
    i client vecchi si perdono."""
    _modo(monkeypatch, "xsendfile")
    esito = consegna.prepara(radice / "città.txt", "città.txt")

    disposizione = esito.intestazioni["Content-Disposition"]
    assert disposizione.startswith("attachment; ")
    assert "filename=" in disposizione
    assert "filename*=UTF-8''citt%C3%A0.txt" in disposizione


def test_le_virgolette_nel_nome_non_spezzano_lintestazione(
    monkeypatch: pytest.MonkeyPatch, radice: Path
) -> None:
    _modo(monkeypatch, "xsendfile")
    nome = 'strano".txt'
    esito = consegna.prepara(radice / nome, nome)

    # Una virgoletta non sfuggita chiuderebbe il campo in anticipo, e il resto
    # del nome verrebbe letto come un altro parametro.
    assert esito.intestazioni["Content-Disposition"].count('"') == 2
