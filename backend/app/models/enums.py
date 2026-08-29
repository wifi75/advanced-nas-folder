"""Enumerazioni condivise dai modelli."""

from enum import StrEnum


class StatoMount(StrEnum):
    """Stato di una condivisione NFS gestita dal pannello."""

    CONFIGURATO = "configurato"  # unit generata, mai montata
    MONTATO = "montato"
    SMONTATO = "smontato"
    ERRORE = "errore"


class AccessoNFS(StrEnum):
    """Modo di accesso richiesto per un mount.

    Attenzione: e cio che il pannello *chiede*. Cio che il NAS concede davvero
    puo essere diverso, ed e registrato separatamente in `effective_read_write`.
    """

    SOLA_LETTURA = "ro"
    LETTURA_SCRITTURA = "rw"


class Visibilita(StrEnum):
    """Chi puo accedere a un percorso pubblicato."""

    PUBBLICA = "pubblica"
    PASSWORD = "password"  # noqa: S105 - nome di una modalita, non una password
    UTENTI = "utenti"  # solo utenti autenticati
    NEGATA = "negata"


class TipoTrasferimento(StrEnum):
    DOWNLOAD = "download"
    UPLOAD = "upload"


class StatoTrasferimento(StrEnum):
    IN_CORSO = "in_corso"
    COMPLETATO = "completato"
    INTERROTTO = "interrotto"
    FALLITO = "fallito"


class WebServer(StrEnum):
    APACHE = "apache"
    NGINX = "nginx"
