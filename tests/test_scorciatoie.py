"""Test degli indirizzi corti verso le cartelle pubblicate."""

import pytest
from anf_agent import webserver
from anf_agent.protocol import ErroreAgent


def test_una_regola_per_pubblicazione() -> None:
    """Mai una regola che cattura tutto: il sito ospita anche altro, e una
    regola generica ne oscurerebbe i contenuti in silenzio."""
    regole = webserver._regole_apache("/", "documenti")

    assert "^/documenti$" in regole
    assert "^/documenti/(.*)$" in regole
    assert "^/(.*)" not in regole


def test_si_usa_mod_alias_e_non_mod_rewrite() -> None:
    """Il file sta fuori dai VirtualHost, e le regole di mod_rewrite non vengono
    ereditate dai VirtualHost mentre quelle di mod_alias si: con RewriteRule le
    scorciatoie rispondevano 404 su ogni sito servito da un vhost, cioe sempre."""
    regole = webserver._regole_apache("/", "documenti")

    assert "RedirectMatch" in regole
    assert "RewriteRule" not in regole


def test_la_destinazione_passa_dal_pannello() -> None:
    assert "/pannello/archivio/documenti" in webserver._regole_apache("/", "documenti")


def test_il_prefisso_del_sito_viene_rispettato() -> None:
    assert "/nas/pannello/archivio/foto" in webserver._regole_apache("/nas/", "foto")


@pytest.mark.parametrize("nome", ["pannello", "api"])
def test_i_nomi_del_pannello_non_diventano_scorciatoie(nome: str) -> None:
    """Una scorciatoia `/pannello` renderebbe il pannello irraggiungibile, e a
    quel punto non ci sarebbe piu modo di toglierla dal pannello stesso."""
    with pytest.raises(ErroreAgent, match="gia usato"):
        webserver._valida_slug(nome)


@pytest.mark.parametrize("nome", ["con spazio", "../altrove", "a/b", "punto.punto"])
def test_un_nome_non_adatto_a_un_indirizzo_viene_rifiutato(nome: str) -> None:
    with pytest.raises(ErroreAgent):
        webserver._valida_slug(nome)


def test_un_nome_normale_passa() -> None:
    assert webserver._valida_slug("foto_2026-estate") == "foto_2026-estate"


async def test_nginx_dice_di_no_invece_di_scrivere_male() -> None:
    """Su Nginx le `location` vanno dentro il blocco `server`: un file a se
    non sarebbe valido, e generarlo farebbe fallire il test di sintassi a ogni
    pubblicazione."""
    with pytest.raises(ErroreAgent, match="solo su Apache"):
        webserver.scorciatoie(webserver="nginx", slug=["documenti"])
