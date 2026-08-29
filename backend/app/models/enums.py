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
    """Chi puo accedere a un percorso pubblicato.

    E la regola di base del percorso. I permessi assegnati al singolo utente
    la sovrascrivono: vedere `PermessoUtente`.
    """

    #: Chiunque, senza accedere al pannello. E l'accesso anonimo.
    PUBBLICA = "pubblica"
    PASSWORD = "password"  # noqa: S105 - nome di una modalita, non una password
    #: Qualunque utente autenticato.
    UTENTI = "utenti"
    #: Solo gli utenti a cui e stato assegnato un permesso esplicito.
    UTENTI_SCELTI = "utenti_scelti"
    NEGATA = "negata"


class Livello(StrEnum):
    """Cosa puo fare un utente su un percorso.

    `NEGATO` non e l'assenza di permesso: e un divieto esplicito, e vince
    sulla regola di base del percorso. Serve a togliere a una persona una
    cartella dentro un ramo che per tutti gli altri resta accessibile.
    """

    NEGATO = "negato"
    LETTURA = "lettura"
    SCRITTURA = "scrittura"


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
