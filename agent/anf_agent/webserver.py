"""Configurazione di Apache e Nginx per una pubblicazione.

Perche generarla invece di lasciarla scrivere a mano: la parte che fa
funzionare i download e proprio quella che si sbaglia piu facilmente. In
Apache serve `XSendFilePath` sulla radice dei mount, in Nginx una `location`
marcata `internal` che nessuno deve poter chiamare dall'esterno. Se manca,
l'utente vede risposte vuote e non capisce perche; se e scritta male, i file
del NAS diventano pubblici senza passare dai permessi.

Ogni scrittura e seguita dal test di sintassi del web server, e **se il test
non passa la configurazione precedente viene rimessa al suo posto**. Un
pannello che puo lasciare il web server in uno stato che non riparte e un
pannello che prima o poi mette fuori uso il server.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from anf_agent.comandi import esegui
from anf_agent.protocol import CodiceErrore, ErroreAgent

logger = logging.getLogger("anf.agent.webserver")

MARCATORE = "# Generato da Advanced NAS Folder - non modificare a mano"


@dataclass(frozen=True, slots=True)
class Impianto:
    """Dove vivono i file di un web server e come si controlla."""

    #: Cartella dei siti disponibili.
    cartella: Path
    #: Cartella dei collegamenti ai siti attivi, se il web server la usa.
    cartella_attivi: Path | None
    estensione: str
    #: Comando che verifica la sintassi senza applicare nulla.
    test: list[str]
    #: Comando che applica la configurazione senza interrompere le connessioni.
    ricarica: list[str]
    #: Comando che dice se il web server e installato.
    presenza: list[str]


IMPIANTI: dict[str, Impianto] = {
    "apache": Impianto(
        cartella=Path("/etc/apache2/sites-available"),
        cartella_attivi=Path("/etc/apache2/sites-enabled"),
        estensione=".conf",
        test=["apache2ctl", "configtest"],
        ricarica=["systemctl", "reload", "apache2"],
        presenza=["apache2ctl", "-v"],
    ),
    "nginx": Impianto(
        cartella=Path("/etc/nginx/sites-available"),
        cartella_attivi=Path("/etc/nginx/sites-enabled"),
        estensione="",
        test=["nginx", "-t"],
        ricarica=["systemctl", "reload", "nginx"],
        presenza=["nginx", "-v"],
    ),
}


_APACHE = """{marcatore}
<VirtualHost *:80>
    ServerName {hostname}

    # Consegna dei file delegata al web server: Python autorizza, Apache
    # invia. Senza queste due righe l'API risponde con un corpo vuoto.
    XSendFile On
    XSendFilePath {radice_mount}

    Alias {prefisso}pannello {cartella_pannello}
    <Directory {cartella_pannello}>
        Require all granted
        Options -Indexes
        # Il pannello e un'applicazione a pagina singola: gli indirizzi interni
        # non corrispondono a file, e senza questa riga darebbero 404 se
        # ricaricati.
        FallbackResource {prefisso}pannello/index.html
    </Directory>

    ProxyPreserveHost On
    ProxyPass {prefisso}api http://127.0.0.1:{porta}/api
    ProxyPassReverse {prefisso}api http://127.0.0.1:{porta}/api

    RedirectMatch ^{prefisso}$ {prefisso}pannello/

    ErrorLog ${{APACHE_LOG_DIR}}/anf-{nome}-error.log
    CustomLog ${{APACHE_LOG_DIR}}/anf-{nome}-access.log combined
</VirtualHost>
"""

_NGINX = """{marcatore}
server {{
    listen 80;
    server_name {hostname};

    # Nessun limite alla dimensione di cio che si carica: il valore
    # predefinito di Nginx e 1 MB, e farebbe fallire qualunque caricamento
    # verso il NAS con un errore che non nomina la causa.
    client_max_body_size 0;

    location = {prefisso} {{
        return 301 {prefisso}pannello/;
    }}

    location {prefisso}pannello/ {{
        alias {cartella_pannello}/;
        try_files $uri $uri/ {prefisso}pannello/index.html;
    }}

    location {prefisso}api/ {{
        proxy_pass http://127.0.0.1:{porta}/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Un download lungo non deve essere interrotto dal proxy.
        proxy_read_timeout 3600s;
    }}

    # Consegna dei file: `internal` significa che questa location risponde solo
    # a una X-Accel-Redirect dell'applicazione, mai a una richiesta esterna.
    # Toglierla renderebbe l'intero NAS pubblico senza passare dai permessi.
    location {prefisso_interno}/ {{
        internal;
        alias {radice_mount}/;
    }}

    access_log /var/log/nginx/anf-{nome}-access.log;
    error_log /var/log/nginx/anf-{nome}-error.log;
}}
"""


def _impianto(webserver: str) -> Impianto:
    impianto = IMPIANTI.get(webserver)
    if impianto is None:
        raise ErroreAgent(CodiceErrore.VALIDAZIONE, f"Web server {webserver!r} non gestito.")
    return impianto


def installati() -> list[str]:
    """Quali web server risultano installati su questa macchina."""
    return [nome for nome, i in IMPIANTI.items() if esegui(i.presenza, timeout=10).riuscito]


def _percorso(impianto: Impianto, hostname: str) -> Path:
    """File di configurazione del vhost. Il nome deriva dall'hostname validato."""
    return impianto.cartella / f"anf-{hostname}{impianto.estensione}"


def _e_nostra(percorso: Path) -> bool:
    try:
        return MARCATORE in percorso.read_text(encoding="utf-8")
    except OSError:
        return False


def rendi(
    *,
    webserver: str,
    hostname: str,
    prefisso: str,
    porta: int,
    cartella_pannello: PurePosixPath,
    radice_mount: PurePosixPath,
    prefisso_interno: str,
) -> str:
    """Costruisce il testo della configurazione, senza scrivere nulla.

    Separata dalla scrittura di proposito: cosi l'API puo mostrare in anteprima
    cio che verrebbe scritto, e i test possono verificarla senza toccare il
    sistema.
    """
    modello = _APACHE if webserver == "apache" else _NGINX
    return modello.format(
        marcatore=MARCATORE,
        hostname=hostname,
        prefisso=prefisso,
        porta=porta,
        cartella_pannello=cartella_pannello,
        radice_mount=radice_mount,
        prefisso_interno=prefisso_interno.rstrip("/"),
        nome=hostname,
    )


def _verifica(impianto: Impianto) -> tuple[bool, str]:
    esito = esegui(impianto.test, timeout=30)
    # Apache e Nginx scrivono l'esito del test su stderr anche quando va bene.
    return esito.riuscito, (esito.stderr or esito.stdout).strip()


def _attiva(impianto: Impianto, percorso: Path) -> None:
    """Collega il sito fra quelli attivi, se il web server usa quella cartella."""
    if impianto.cartella_attivi is None:
        return
    collegamento = impianto.cartella_attivi / percorso.name
    if collegamento.is_symlink() or collegamento.exists():
        return
    collegamento.symlink_to(percorso)


def _disattiva(impianto: Impianto, percorso: Path) -> None:
    if impianto.cartella_attivi is None:
        return
    collegamento = impianto.cartella_attivi / percorso.name
    if collegamento.is_symlink():
        collegamento.unlink()


def _ripristina(percorso: Path, precedente: str | None, impianto: Impianto) -> None:
    """Rimette la configurazione com'era prima del tentativo fallito."""
    if precedente is None:
        _disattiva(impianto, percorso)
        percorso.unlink(missing_ok=True)
    else:
        percorso.write_text(precedente, encoding="utf-8")


def scrivi(*, webserver: str, hostname: str, contenuto: str, attiva: bool = True) -> dict[str, str]:
    """Scrive il vhost, lo prova e **lo ripristina se la prova fallisce**.

    Restituisce l'uscita del test di sintassi: e l'unica cosa che spiega
    davvero cosa non andava, e mostrarla nel pannello evita di dover leggere i
    log del server per capirlo.
    """
    impianto = _impianto(webserver)
    if not impianto.cartella.is_dir():
        raise ErroreAgent(
            CodiceErrore.NON_TROVATO,
            f"{impianto.cartella} non esiste: {webserver} non sembra installato.",
        )

    percorso = _percorso(impianto, hostname)
    if percorso.exists() and not _e_nostra(percorso):
        raise ErroreAgent(
            CodiceErrore.VALIDAZIONE,
            f"{percorso.name} esiste ma non e stato generato da questo pannello: "
            "non viene sovrascritto.",
        )

    precedente = percorso.read_text(encoding="utf-8") if percorso.exists() else None
    percorso.write_text(contenuto, encoding="utf-8")
    percorso.chmod(0o644)
    if attiva:
        _attiva(impianto, percorso)

    passato, uscita = _verifica(impianto)
    if not passato:
        _ripristina(percorso, precedente, impianto)
        logger.warning("configurazione rifiutata per %s, ripristinata: %s", hostname, uscita)
        raise ErroreAgent(
            CodiceErrore.COMANDO_FALLITO,
            f"La configurazione non e valida ed e stata annullata. {webserver} dice: {uscita}",
        )

    ricaricato = esegui(impianto.ricarica, timeout=30)
    if not ricaricato.riuscito:
        # Qui la sintassi era buona: il problema e altrove (servizio fermo,
        # porta occupata). Non si ripristina, perche non e questo file a essere
        # sbagliato, ma lo si dice.
        raise ErroreAgent(
            CodiceErrore.COMANDO_FALLITO,
            f"Configurazione scritta, ma il ricaricamento e fallito: {ricaricato.messaggio_errore}",
        )

    return {"percorso": str(percorso), "test": uscita}


def rimuovi(*, webserver: str, hostname: str) -> dict[str, str]:
    """Toglie un vhost generato da noi. Non tocca i file di altri."""
    impianto = _impianto(webserver)
    percorso = _percorso(impianto, hostname)

    if not percorso.exists():
        return {"percorso": str(percorso), "rimosso": "no"}
    if not _e_nostra(percorso):
        raise ErroreAgent(
            CodiceErrore.VALIDAZIONE,
            f"{percorso.name} non e stato generato da questo pannello: non viene rimosso.",
        )

    _disattiva(impianto, percorso)
    percorso.unlink()

    passato, uscita = _verifica(impianto)
    if passato:
        esegui(impianto.ricarica, timeout=30)
    return {"percorso": str(percorso), "rimosso": "si", "test": uscita}


def elenca(webserver: str) -> list[str]:
    """Gli hostname dei vhost generati da questo pannello."""
    impianto = _impianto(webserver)
    if not impianto.cartella.is_dir():
        return []
    return sorted(
        f.name.removeprefix("anf-").removesuffix(impianto.estensione)
        for f in impianto.cartella.glob(f"anf-*{impianto.estensione}")
        if _e_nostra(f)
    )


# --- scorciatoie sulla radice del sito --------------------------------------

#: Nomi che non possono diventare una scorciatoia perche il sito li usa gia.
#: L'elenco e volutamente corto: sono i percorsi che questa applicazione stessa
#: occupa. Tutto il resto e responsabilita di chi sceglie l'identificatore.
RISERVATI = frozenset({"pannello", "api", "server-status", "server-info"})

_SCORCIATOIE_APACHE = """{marcatore}
# Scorciatoie: /nome porta alla cartella pubblicata con quel nome.
#
# Sono redirezioni, non riscritture interne: il pannello e una applicazione a
# pagina singola servita sotto /pannello/, e il suo router non riconoscerebbe
# un indirizzo che parte dalla radice. Con la redirezione l'indirizzo corto
# funziona da subito — nei link, nei preferiti, scritto a mano — e il browser
# prosegue su quello lungo.
#
# Si usa RedirectMatch e non RewriteRule: questo file sta fuori dai
# VirtualHost, e le regole di mod_rewrite **non** vengono ereditate dai
# VirtualHost, mentre quelle di mod_alias si. Con RewriteRule le scorciatoie
# rispondevano 404 su ogni sito servito da un vhost, cioe sempre.
#
# Viene generata una regola per ogni pubblicazione, mai una regola che cattura
# tutto: cosi nessun altro contenuto di questo sito viene oscurato per sbaglio.
{regole}"""


def _regole_apache(prefisso: str, slug: str) -> str:
    destinazione = f"{prefisso}pannello/archivio/{slug}"
    return (
        f"RedirectMatch 302 ^/{slug}$ {destinazione}\n"
        f"RedirectMatch 302 ^/{slug}/(.*)$ {destinazione}/$1\n"
    )


def _valida_slug(slug: object) -> str:
    if not isinstance(slug, str) or not slug:
        raise ErroreAgent(CodiceErrore.VALIDAZIONE, "Identificatore mancante.")
    if not all(c.isalnum() or c in "-_" for c in slug):
        raise ErroreAgent(
            CodiceErrore.VALIDAZIONE,
            f"{slug!r} contiene caratteri non ammessi in un indirizzo.",
        )
    if slug in RISERVATI:
        raise ErroreAgent(
            CodiceErrore.VALIDAZIONE,
            f"{slug!r} e gia usato dal pannello: scegliere un altro identificatore.",
        )
    return slug


def scorciatoie(*, webserver: str, slug: list[str], prefisso: str = "/") -> dict[str, str]:
    """Riscrive per intero il file delle scorciatoie.

    Riceve l'elenco completo invece di aggiunte e rimozioni: il file generato
    e allora sempre uguale allo stato del database, e una scorciatoia rimasta
    indietro non puo sopravvivere alla pubblicazione che l'aveva creata.
    """
    # Su Nginx le `location` devono stare dentro il blocco `server`: un file a
    # se non sarebbe configurazione valida, e generarlo lo stesso vorrebbe dire
    # far fallire il test di sintassi a ogni pubblicazione. Le scorciatoie per
    # Nginx richiedono di rigenerare il vhost, che e lavoro diverso da questo.
    if webserver != "apache":
        raise ErroreAgent(
            CodiceErrore.VALIDAZIONE,
            "Le scorciatoie sono disponibili solo su Apache.",
        )

    impianto = _impianto(webserver)
    if not impianto.cartella.is_dir():
        raise ErroreAgent(
            CodiceErrore.NON_TROVATO,
            f"{impianto.cartella} non esiste: {webserver} non sembra installato.",
        )

    validi = [_valida_slug(s) for s in slug]
    regole = "".join(_regole_apache(prefisso, s) for s in validi)
    contenuto = _SCORCIATOIE_APACHE.format(marcatore=MARCATORE, regole=regole)

    percorso = impianto.cartella / f"anf-scorciatoie{impianto.estensione}"
    if percorso.exists() and not _e_nostra(percorso):
        raise ErroreAgent(
            CodiceErrore.VALIDAZIONE,
            f"{percorso.name} esiste ma non e stato generato da questo pannello.",
        )

    precedente = percorso.read_text(encoding="utf-8") if percorso.exists() else None
    percorso.write_text(contenuto, encoding="utf-8")
    percorso.chmod(0o644)
    _attiva(impianto, percorso)

    passato, uscita = _verifica(impianto)
    if not passato:
        _ripristina(percorso, precedente, impianto)
        logger.warning("scorciatoie rifiutate, ripristinate: %s", uscita)
        raise ErroreAgent(
            CodiceErrore.COMANDO_FALLITO,
            f"Le scorciatoie non sono state applicate. {webserver} dice: {uscita}",
        )

    esegui(impianto.ricarica, timeout=30)
    return {"percorso": str(percorso), "quante": str(len(validi)), "test": uscita}
