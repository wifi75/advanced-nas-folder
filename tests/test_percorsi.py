"""Test della barriera sui percorsi.

Ogni percorso che arriva da una richiesta HTTP passa da qui: se cede, il
pannello serve l'intero disco invece della cartella pubblicata.
"""

import os
from pathlib import Path, PurePosixPath

import pytest
from app.services.percorsi import (
    PercorsoNonValido,
    dentro,
    e_nascosto,
    normalizza_relativo,
    risolvi,
)


@pytest.mark.parametrize(
    ("dato", "atteso"),
    [
        (None, ""),
        ("", ""),
        ("/", ""),
        ("foto", "foto"),
        ("/foto", "foto"),
        ("foto/", "foto"),
        ("foto//cucina", "foto/cucina"),
        ("./foto/./cucina", "foto/cucina"),
        ("foto\\cucina", "foto/cucina"),
    ],
)
def test_normalizzazione(dato: str | None, atteso: str) -> None:
    assert str(normalizza_relativo(dato)) == (atteso or ".")


@pytest.mark.parametrize(
    "malevolo",
    [
        "../etc/passwd",
        "foto/../../etc",
        "/../etc",
        "foto/..",
        "..",
        "foto/\x00nascosto",
        "foto\nnuova-riga",
        "foto\rritorno",
    ],
)
def test_percorsi_malevoli_respinti(malevolo: str) -> None:
    with pytest.raises(PercorsoNonValido):
        normalizza_relativo(malevolo)


def test_risoluzione_dentro_la_radice(tmp_path: Path) -> None:
    (tmp_path / "foto").mkdir()
    assert risolvi(tmp_path, "foto") == (tmp_path / "foto").resolve()
    assert risolvi(tmp_path, "") == tmp_path.resolve()


def test_risoluzione_rifiuta_la_risalita(tmp_path: Path) -> None:
    with pytest.raises(PercorsoNonValido):
        risolvi(tmp_path, "../fuori")


def test_collegamento_che_esce_viene_rifiutato(tmp_path: Path) -> None:
    """Un collegamento dentro la cartella che punta fuori è l'aggiramento più
    semplice di un controllo fatto solo sulla stringa: va bloccato sul
    percorso risolto."""
    radice = tmp_path / "condivisa"
    radice.mkdir()
    fuori = tmp_path / "riservato"
    fuori.mkdir()
    (fuori / "segreti.txt").write_text("dati", encoding="utf-8")

    try:
        os.symlink(fuori, radice / "scorciatoia", target_is_directory=True)
    except OSError, NotImplementedError:
        pytest.skip("creazione di collegamenti simbolici non consentita")

    with pytest.raises(PercorsoNonValido):
        risolvi(radice, "scorciatoia/segreti.txt")


def test_dentro(tmp_path: Path) -> None:
    (tmp_path / "a" / "b").mkdir(parents=True)
    assert dentro(tmp_path, tmp_path / "a" / "b")
    assert dentro(tmp_path, tmp_path)
    assert not dentro(tmp_path / "a", tmp_path)


@pytest.mark.parametrize(
    ("percorso", "atteso"),
    [("foto/cucina", False), (".nascosto", True), ("foto/.git/config", True), ("", False)],
)
def test_file_nascosti(percorso: str, atteso: bool) -> None:
    assert e_nascosto(PurePosixPath(*normalizza_relativo(percorso).parts)) is atteso
