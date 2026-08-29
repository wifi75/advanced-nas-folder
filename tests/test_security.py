"""Test di hash delle password e token di accesso."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.core.config import get_settings
from app.core.security import (
    ALGORITMO,
    crea_access_token,
    decodifica_token,
    hash_password,
    verifica_password,
)


def test_hash_diverso_a_ogni_chiamata() -> None:
    """Due hash della stessa password devono differire: il sale e casuale."""
    assert hash_password("segreta") != hash_password("segreta")


def test_password_corretta_verificata() -> None:
    assert verifica_password("segreta", hash_password("segreta"))


@pytest.mark.parametrize("sbagliata", ["Segreta", "segret", "segreta ", "", "altro"])
def test_password_sbagliata_respinta(sbagliata: str) -> None:
    assert not verifica_password(sbagliata, hash_password("segreta"))


def test_hash_malformato_non_solleva() -> None:
    """Un valore corrotto nel database deve dare 'no', non far cadere il login."""
    assert not verifica_password("qualunque", "questo-non-e-un-hash")


def test_token_contiene_il_soggetto() -> None:
    contenuto = decodifica_token(crea_access_token("42"))
    assert contenuto is not None
    assert contenuto["sub"] == "42"


def test_token_manomesso_respinto() -> None:
    token = crea_access_token("1")
    testa, corpo, firma = token.split(".")
    manomesso = f"{testa}.{corpo}.{'a' * len(firma)}"
    assert decodifica_token(manomesso) is None


def test_token_firmato_con_altra_chiave_respinto() -> None:
    estraneo = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) + timedelta(hours=1)},
        # Lunga almeno 32 byte: una chiave corta farebbe fallire il test per il
        # motivo sbagliato, cioe la lunghezza invece della firma.
        "chiave-di-qualcun-altro-abbastanza-lunga-da-essere-accettata",
        algorithm=ALGORITMO,
    )
    assert decodifica_token(estraneo) is None


def test_token_scaduto_respinto() -> None:
    scaduto = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        get_settings().secret_key,
        algorithm=ALGORITMO,
    )
    assert decodifica_token(scaduto) is None


def test_token_senza_scadenza_respinto() -> None:
    """Un token senza 'exp' non scadrebbe mai: va rifiutato."""
    perenne = jwt.encode({"sub": "1"}, get_settings().secret_key, algorithm=ALGORITMO)
    assert decodifica_token(perenne) is None


def test_token_illeggibile_respinto() -> None:
    assert decodifica_token("non.e.un.token") is None
