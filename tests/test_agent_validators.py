"""Test della barriera di sicurezza dell'agent.

Questi test sono la parte piu importante della suite: l'agent gira da root, e
ogni valore che supera i validatori raggiunge il sistema. Verificano il
comportamento che conta davvero, cioe che gli input malevoli vengano RIFIUTATI.
"""

from pathlib import PurePosixPath

import pytest
from anf_agent.protocol import CodiceErrore, ErroreAgent, Richiesta, Verbo
from anf_agent.validators import (
    mountpoint_per,
    valida_opzioni,
    valida_percorso_export,
    valida_server,
    valida_slug,
    valida_versione_nfs,
)

RADICE = PurePosixPath("/srv/nas")


# --- slug ---


@pytest.mark.parametrize("valido", ["zipped", "foto-cucina", "a", "n0me-con-9"])
def test_slug_validi(valido: str) -> None:
    assert valida_slug(valido) == valido


@pytest.mark.parametrize(
    "malevolo",
    [
        "../../etc",
        "a/b",
        "-inizia-con-trattino",
        "MAIUSCOLE",
        "con spazio",
        "con.punto",
        "",
        "x" * 64,
        "nome\x00nullo",
        None,
        123,
    ],
)
def test_slug_rifiutati(malevolo: object) -> None:
    with pytest.raises(ErroreAgent) as errore:
        valida_slug(malevolo)
    assert errore.value.codice is CodiceErrore.VALIDAZIONE


# --- percorso del mount: non deve MAI uscire dalla radice ---


def test_mountpoint_resta_sotto_la_radice() -> None:
    assert mountpoint_per("zipped", RADICE) == PurePosixPath("/srv/nas/zipped")


@pytest.mark.parametrize("fuga", ["..", "../../etc", "/etc", "a/../../b"])
def test_mountpoint_non_puo_evadere(fuga: str) -> None:
    with pytest.raises(ErroreAgent):
        mountpoint_per(fuga, RADICE)


# --- indirizzo del server ---


@pytest.mark.parametrize("valido", ["192.168.1.10", "10.0.0.1", "nas.locale", "fd00::1"])
def test_server_validi(valido: str) -> None:
    assert valida_server(valido) == valido


@pytest.mark.parametrize(
    "malevolo",
    [
        "ciao; rm -rf /",
        "nas && reboot",
        "$(whoami)",
        "`id`",
        "nas|cat /etc/shadow",
        "nas locale",
        "",
        None,
    ],
)
def test_server_rifiutati(malevolo: object) -> None:
    with pytest.raises(ErroreAgent):
        valida_server(malevolo)


# --- percorso esportato ---


def test_export_normalizzato() -> None:
    assert valida_percorso_export("/volume2/Zipped/") == "/volume2/Zipped"


@pytest.mark.parametrize(
    "malevolo",
    ["/volume2/../etc", "relativo/senza/barra", "", "/con\x00nullo", None, 42],
)
def test_export_rifiutati(malevolo: object) -> None:
    with pytest.raises(ErroreAgent):
        valida_percorso_export(malevolo)


# --- opzioni di mount: whitelist ---


def test_opzioni_ammesse() -> None:
    opzioni = valida_opzioni(["ro", "noatime", "vers=3", "timeo=150", "proto=tcp"])
    assert opzioni == ["ro", "noatime", "vers=3", "timeo=150", "proto=tcp"]


@pytest.mark.parametrize(
    "malevola",
    [
        ["exec"],
        ["suid"],
        ["ro,rw"],
        ["timeo=abc"],
        ["timeo=999999"],
        ["proto=carbonpigeon"],
        ["vers=9"],
        ["ro", "ro"],
        ["ro", "rw"],
        [""],
        [None],
        "non-una-lista",
    ],
)
def test_opzioni_rifiutate(malevola: object) -> None:
    with pytest.raises(ErroreAgent):
        valida_opzioni(malevola)


def test_versione_nfs() -> None:
    assert valida_versione_nfs(None) == "3"
    assert valida_versione_nfs("4.1") == "4.1"
    with pytest.raises(ErroreAgent):
        valida_versione_nfs("4.9")


# --- protocollo: insieme chiuso di verbi ---


def test_verbo_valido() -> None:
    richiesta = Richiesta.da_json(b'{"verbo": "ping", "dati": {}}')
    assert richiesta.verbo is Verbo.PING


@pytest.mark.parametrize(
    "grezzo",
    [
        b'{"verbo": "mount.esegui_qualsiasi_cosa"}',
        b'{"verbo": "shell"}',
        b'{"verbo": null}',
        b'{"nessun_verbo": 1}',
    ],
)
def test_verbi_sconosciuti_rifiutati(grezzo: bytes) -> None:
    with pytest.raises(ErroreAgent) as errore:
        Richiesta.da_json(grezzo)
    assert errore.value.codice is CodiceErrore.VERBO_SCONOSCIUTO


@pytest.mark.parametrize(
    "grezzo", [b"non json", b"[]", b'"stringa"', b'{"verbo": "ping", "dati": 5}']
)
def test_richieste_malformate_rifiutate(grezzo: bytes) -> None:
    with pytest.raises(ErroreAgent) as errore:
        Richiesta.da_json(grezzo)
    assert errore.value.codice in {
        CodiceErrore.RICHIESTA_MALFORMATA,
        CodiceErrore.VERBO_SCONOSCIUTO,
    }
