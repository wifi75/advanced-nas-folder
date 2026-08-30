"""Controlli sui testi dell'interfaccia.

Perche' stanno qui e non in un test del frontend: il progetto non ha un runner
di test JavaScript, e aggiungerne uno per questo controllo sarebbe una
dipendenza in piu' da mantenere. Il formato dei file di traduzione e' regolare
abbastanza da leggerlo senza interprete.

Nascono da un difetto vero: le chiavi di alcuni pulsanti erano finite nel blocco
sbagliato, e il pannello mostrava «share.modifica» al posto di «Modifica». Il
build passava, i tipi passavano, il lint passava: una chiave mancante si vede
solo aprendo quella pagina.
"""

import re
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[1] / "frontend" / "src"
LINGUE = {"it": RADICE / "i18n" / "it.ts", "en": RADICE / "i18n" / "en.ts"}

#: `t('qualcosa.chiave')`, escludendo le chiavi costruite a pezzi — quelle
#: contengono `${` e non sono verificabili senza eseguire il codice.
USO = re.compile(r"[^a-zA-Z]t\(\s*'([a-zA-Z0-9_.]+)'")


def _definite(sorgente: str) -> set[str]:
    """Le chiavi definite, in notazione puntata, lette dall'indentazione."""
    chiavi: set[str] = set()
    percorso: list[str] = []
    for riga in sorgente.split("\n"):
        spogliata = riga.strip()
        if not spogliata or spogliata.startswith("//"):
            continue
        livello = (len(riga) - len(riga.lstrip())) // 2
        if apertura := re.match(r"([a-zA-Z0-9_]+): \{$", spogliata):
            percorso = percorso[: livello - 1] + [apertura.group(1)]
        elif foglia := re.match(r"([a-zA-Z0-9_]+):", spogliata):
            chiavi.add(".".join(percorso[: livello - 1] + [foglia.group(1)]))
    return chiavi


def _usate() -> set[str]:
    chiavi: set[str] = set()
    for file in [*RADICE.rglob("*.vue"), *RADICE.rglob("*.ts")]:
        if file.parent.name == "i18n":
            continue
        chiavi |= set(USO.findall(file.read_text(encoding="utf-8")))
    return chiavi


@pytest.mark.parametrize("lingua", sorted(LINGUE))
def test_ogni_chiave_usata_esiste(lingua: str) -> None:
    """Una chiave mancante non rompe niente: stampa se stessa a schermo."""
    definite = _definite(LINGUE[lingua].read_text(encoding="utf-8"))
    mancanti = sorted(k for k in _usate() if k not in definite)

    assert not mancanti, f"chiavi usate ma non definite in {lingua}: {mancanti}"


def test_le_due_lingue_hanno_le_stesse_chiavi() -> None:
    """Una chiave presente solo in italiano lascia l'inglese con il codice a
    schermo, e nessuno se ne accorge finche' non cambia lingua."""
    it = _definite(LINGUE["it"].read_text(encoding="utf-8"))
    en = _definite(LINGUE["en"].read_text(encoding="utf-8"))

    assert sorted(it - en) == [], "presenti solo in italiano"
    assert sorted(en - it) == [], "presenti solo in inglese"
