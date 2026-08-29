"""Test della configurazione generata per Apache e Nginx.

Due cose contano qui, e sono entrambe cose che si scoprirebbero tardi:
la configurazione deve contenere le direttive che fanno funzionare i download,
e una configurazione rifiutata dal web server non deve **restare** sul disco.
"""

from pathlib import Path, PurePosixPath

import pytest
from anf_agent import webserver
from anf_agent.comandi import Esito
from anf_agent.protocol import CodiceErrore, ErroreAgent
from anf_agent.validators import (
    valida_cartella_assoluta,
    valida_hostname,
    valida_porta,
    valida_prefisso_url,
    valida_webserver,
)


def _rendi(ws: str) -> str:
    return webserver.rendi(
        webserver=ws,
        hostname="archivio.esempio.it",
        prefisso="/",
        porta=8100,
        cartella_pannello=PurePosixPath("/var/www/anf/pannello"),
        radice_mount=PurePosixPath("/srv/nas"),
        prefisso_interno="/__anf_internal/",
    )


# --- validatori ------------------------------------------------------------


@pytest.mark.parametrize(
    "cattivo",
    [
        "archivio.esempio.it/../../etc",
        "archivio esempio",
        "archivio;rm -rf /",
        "-archivio.it",
        "",
        None,
        123,
    ],
)
def test_hostname_malevoli_rifiutati(cattivo: object) -> None:
    """L'hostname finisce nel nome del file: qui si decide dove l'agent scrive."""
    with pytest.raises(ErroreAgent) as errore:
        valida_hostname(cattivo)
    assert errore.value.codice is CodiceErrore.VALIDAZIONE


def test_hostname_normalizzato_in_minuscolo() -> None:
    assert valida_hostname("  Archivio.Esempio.IT ") == "archivio.esempio.it"


@pytest.mark.parametrize(
    ("dato", "atteso"),
    [(None, "/"), ("", "/"), ("/", "/"), ("nas", "/nas/"), ("/nas/", "/nas/"), ("a/b", "/a/b/")],
)
def test_prefisso_ridotto_a_forma_canonica(dato: object, atteso: str) -> None:
    assert valida_prefisso_url(dato) == atteso


@pytest.mark.parametrize("cattivo", ["../etc", "/nas/../..", "/nas/{}", "/nas/ x", 5])
def test_prefissi_malevoli_rifiutati(cattivo: object) -> None:
    with pytest.raises(ErroreAgent):
        valida_prefisso_url(cattivo)


@pytest.mark.parametrize("cattivo", [0, 70000, "8100", True, None])
def test_porte_non_valide_rifiutate(cattivo: object) -> None:
    with pytest.raises(ErroreAgent):
        valida_porta(cattivo)


@pytest.mark.parametrize(
    "cattivo",
    [
        "relativo/percorso",
        "/var/www/../../etc",
        '/var/www/"a"',
        "/var/www/a\nRequire all granted",
        None,
    ],
)
def test_cartelle_malevole_rifiutate(cattivo: object) -> None:
    """Una virgoletta o un a capo chiuderebbero una direttiva e ne aprirebbero un'altra."""
    with pytest.raises(ErroreAgent):
        valida_cartella_assoluta(cattivo, nome="Cartella")


@pytest.mark.parametrize("cattivo", ["iis", "APACHE", "", None])
def test_webserver_non_gestiti_rifiutati(cattivo: object) -> None:
    with pytest.raises(ErroreAgent):
        valida_webserver(cattivo)


# --- contenuto generato ----------------------------------------------------


def test_apache_abilita_la_consegna_dei_file() -> None:
    """Senza XSendFilePath l'API risponde con un corpo vuoto e nessuno capisce perché."""
    testo = _rendi("apache")
    assert "XSendFile On" in testo
    assert "XSendFilePath /srv/nas" in testo


def test_nginx_tiene_interna_la_consegna_dei_file() -> None:
    """Senza `internal` l'intero NAS sarebbe scaricabile saltando i permessi."""
    testo = _rendi("nginx")
    posizione = testo.index("location /__anf_internal/")
    assert "internal;" in testo[posizione : posizione + 120]
    assert "alias /srv/nas/;" in testo[posizione : posizione + 200]


def test_il_pannello_regge_il_ricaricamento_di_una_pagina_interna() -> None:
    """Gli indirizzi interni non sono file: senza ripiego darebbero 404 se ricaricati."""
    assert "FallbackResource /pannello/index.html" in _rendi("apache")
    assert "try_files $uri $uri/ /pannello/index.html;" in _rendi("nginx")


def test_ogni_configurazione_porta_il_marcatore() -> None:
    """È ciò che permette all'agent di non toccare mai file di altri."""
    assert _rendi("apache").startswith(webserver.MARCATORE)
    assert _rendi("nginx").startswith(webserver.MARCATORE)


# --- scrittura, prova e ripristino -----------------------------------------


@pytest.fixture
def impianto(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> webserver.Impianto:
    """Un web server finto, con le sue cartelle in una directory temporanea."""
    disponibili = tmp_path / "sites-available"
    attivi = tmp_path / "sites-enabled"
    disponibili.mkdir()
    attivi.mkdir()

    finto = webserver.Impianto(
        cartella=disponibili,
        cartella_attivi=attivi,
        estensione=".conf",
        test=["prova"],
        ricarica=["ricarica"],
        presenza=["presenza"],
    )
    monkeypatch.setitem(webserver.IMPIANTI, "apache", finto)
    return finto


def _comandi(monkeypatch: pytest.MonkeyPatch, *, test_passa: bool) -> None:
    def finto(argomenti: list[str], *, timeout: float = 30.0) -> Esito:
        if argomenti == ["prova"] and not test_passa:
            return Esito(1, "", "Syntax error on line 7")
        return Esito(0, "", "Syntax OK")

    monkeypatch.setattr(webserver, "esegui", finto)


def test_una_configurazione_valida_viene_scritta_e_attivata(
    monkeypatch: pytest.MonkeyPatch, impianto: webserver.Impianto
) -> None:
    _comandi(monkeypatch, test_passa=True)
    esito = webserver.scrivi(
        webserver="apache", hostname="archivio.esempio.it", contenuto=_rendi("apache")
    )

    scritto = impianto.cartella / "anf-archivio.esempio.it.conf"
    assert scritto.exists()
    assert esito["test"] == "Syntax OK"
    assert impianto.cartella_attivi is not None
    assert (impianto.cartella_attivi / scritto.name).is_symlink()


def test_una_configurazione_rifiutata_non_resta_sul_disco(
    monkeypatch: pytest.MonkeyPatch, impianto: webserver.Impianto
) -> None:
    """Un pannello che può lasciare il web server incapace di ripartire è un problema."""
    _comandi(monkeypatch, test_passa=False)

    with pytest.raises(ErroreAgent) as errore:
        webserver.scrivi(
            webserver="apache", hostname="archivio.esempio.it", contenuto=_rendi("apache")
        )

    assert "Syntax error on line 7" in errore.value.messaggio
    assert not (impianto.cartella / "anf-archivio.esempio.it.conf").exists()


def test_una_modifica_rifiutata_rimette_la_versione_precedente(
    monkeypatch: pytest.MonkeyPatch, impianto: webserver.Impianto
) -> None:
    _comandi(monkeypatch, test_passa=True)
    webserver.scrivi(webserver="apache", hostname="archivio.esempio.it", contenuto=_rendi("apache"))
    scritto = impianto.cartella / "anf-archivio.esempio.it.conf"
    buona = scritto.read_text(encoding="utf-8")

    _comandi(monkeypatch, test_passa=False)
    with pytest.raises(ErroreAgent):
        webserver.scrivi(
            webserver="apache",
            hostname="archivio.esempio.it",
            contenuto=f"{webserver.MARCATORE}\nrovinata",
        )

    assert scritto.read_text(encoding="utf-8") == buona


def test_un_file_di_altri_non_viene_toccato(
    monkeypatch: pytest.MonkeyPatch, impianto: webserver.Impianto
) -> None:
    """Senza il marcatore il file non è nostro, e sovrascriverlo sarebbe un danno."""
    _comandi(monkeypatch, test_passa=True)
    altrui = impianto.cartella / "anf-archivio.esempio.it.conf"
    altrui.write_text("configurazione scritta a mano", encoding="utf-8")

    with pytest.raises(ErroreAgent):
        webserver.scrivi(
            webserver="apache", hostname="archivio.esempio.it", contenuto=_rendi("apache")
        )
    assert altrui.read_text(encoding="utf-8") == "configurazione scritta a mano"

    with pytest.raises(ErroreAgent):
        webserver.rimuovi(webserver="apache", hostname="archivio.esempio.it")
    assert altrui.exists()


def test_elenca_solo_i_vhost_nostri(
    monkeypatch: pytest.MonkeyPatch, impianto: webserver.Impianto
) -> None:
    _comandi(monkeypatch, test_passa=True)
    webserver.scrivi(webserver="apache", hostname="uno.esempio.it", contenuto=_rendi("apache"))
    (impianto.cartella / "anf-altrui.esempio.it.conf").write_text("altro", encoding="utf-8")

    assert webserver.elenca("apache") == ["uno.esempio.it"]
