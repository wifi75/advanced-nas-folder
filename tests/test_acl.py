"""Test dei permessi per sottocartella."""

import pytest
from app.models import AccessRule, Share, User
from app.models.enums import Visibilita
from app.services.acl import dentro_ambito, regola_applicabile, valuta


def costruisci(
    predefinita: Visibilita = Visibilita.UTENTI, regole: list[tuple[str, Visibilita]] | None = None
) -> Share:
    share = Share(slug="s", label="S", mount_id=1, subpath="", is_enabled=True)
    share.default_visibility = predefinita
    share.rules = [
        AccessRule(path_prefix=p, visibility=v) for p, v in (regole or [])
    ]
    return share


def utente(*, admin: bool = False, scope: str = "") -> User:
    u = User(username="u", password_hash="x")
    u.is_admin = admin
    u.is_active = True
    u.scope = scope
    return u


# --- scelta della regola ---


def test_vince_il_prefisso_piu_lungo() -> None:
    share = costruisci(
        regole=[
            ("", Visibilita.PUBBLICA),
            ("foto", Visibilita.UTENTI),
            ("foto/private", Visibilita.NEGATA),
        ]
    )
    assert regola_applicabile(share, "foto/private/x.jpg").visibility is Visibilita.NEGATA
    assert regola_applicabile(share, "foto/vacanze").visibility is Visibilita.UTENTI
    assert regola_applicabile(share, "documenti").visibility is Visibilita.PUBBLICA


def test_il_prefisso_non_corrisponde_a_meta_nome() -> None:
    """`foto` non deve coprire `fotografie`: il confronto è per cartelle."""
    share = costruisci(predefinita=Visibilita.PUBBLICA, regole=[("foto", Visibilita.NEGATA)])
    assert regola_applicabile(share, "fotografie/x.jpg") is None
    assert valuta(share, "fotografie/x.jpg", None).consentito


# --- decisione ---


def test_sottocartella_piu_restrittiva_della_radice() -> None:
    """È il requisito centrale della fase 2."""
    share = costruisci(
        predefinita=Visibilita.PUBBLICA, regole=[("riservato", Visibilita.UTENTI)]
    )
    assert valuta(share, "pubblico/foto.jpg", None).consentito
    assert not valuta(share, "riservato/nota.txt", None).consentito
    assert valuta(share, "riservato/nota.txt", utente()).consentito


def test_pubblicazione_disattivata_blocca_tutti() -> None:
    share = costruisci(predefinita=Visibilita.PUBBLICA)
    share.is_enabled = False
    assert not valuta(share, "x", utente(admin=True)).consentito


def test_negata_vale_anche_per_amministratore() -> None:
    """Altrimenti quella visibilità non significherebbe nulla."""
    share = costruisci(regole=[("segreto", Visibilita.NEGATA)])
    assert not valuta(share, "segreto/x", utente(admin=True)).consentito


def test_amministratore_supera_le_altre_visibilita() -> None:
    share = costruisci(regole=[("x", Visibilita.PASSWORD)])
    assert valuta(share, "x/file", utente(admin=True)).consentito


def test_password_serve_finche_non_e_fornita() -> None:
    share = costruisci(regole=[("x", Visibilita.PASSWORD)])
    assert not valuta(share, "x/file", None).consentito
    assert valuta(share, "x/file", None, password_fornita=True).consentito


def test_visibilita_utenti_richiede_autenticazione() -> None:
    share = costruisci(predefinita=Visibilita.UTENTI)
    assert not valuta(share, "x", None).consentito
    assert valuta(share, "x", utente()).consentito


def test_il_motivo_e_sempre_valorizzato() -> None:
    """Serve a spiegare il diniego, non a lasciare l'utente al buio."""
    share = costruisci(predefinita=Visibilita.UTENTI)
    assert valuta(share, "x", None).motivo


# --- ambito dell'utente ---


@pytest.mark.parametrize(
    ("ambito", "percorso", "atteso"),
    [
        ("", "qualunque/cosa", True),
        ("foto", "foto/cucina", True),
        ("foto", "foto", True),
        ("foto", "documenti", False),
        ("foto", "fotografie", False),
        ("foto/cucina", "foto", False),
    ],
)
def test_ambito(ambito: str, percorso: str, atteso: bool) -> None:
    assert dentro_ambito(utente(scope=ambito), percorso) is atteso


def test_ambito_non_limita_amministratore() -> None:
    assert dentro_ambito(utente(admin=True, scope="foto"), "documenti")
