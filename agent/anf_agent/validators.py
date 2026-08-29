"""Validazione degli argomenti che arrivano dall'API.

Questo modulo e la barriera di sicurezza dell'intero progetto. L'agent gira da
root: ogni valore che non passa di qui non deve raggiungere il sistema.

Principio: si accetta solo cio che e esplicitamente previsto. Mai "rifiuta i
caratteri pericolosi", che e una lista che si dimentica sempre qualcosa.
"""

from __future__ import annotations

import ipaddress
import re
from pathlib import PurePosixPath

from anf_agent.protocol import CodiceErrore, ErroreAgent

#: Identificatore di un mount. Finisce nel nome della unit systemd e nel
#: percorso di montaggio, quindi e volutamente ristretto.
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")

#: Nome host secondo RFC 1123, senza punto finale.
_HOSTNAME = re.compile(
    r"^(?=.{1,253}$)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)

#: Versioni NFS ammesse.
VERSIONI_NFS = frozenset({"3", "4.0", "4.1", "4.2"})

#: Opzioni di mount consentite e come vanno validate.
#: Un'opzione non presente qui e un errore, non un valore da inoltrare al
#: kernel: e cosi che si evita che l'API possa passare qualunque cosa.
OPZIONI_BOOLEANE = frozenset(
    {
        "ro",
        "rw",
        "noatime",
        "soft",
        "hard",
        "nolock",
        "_netdev",
        "nofail",
        "x-systemd.automount",
    }
)
OPZIONI_NUMERICHE: dict[str, tuple[int, int]] = {
    "timeo": (1, 6000),
    "retrans": (1, 20),
    "x-systemd.mount-timeout": (1, 600),
    "x-systemd.idle-timeout": (0, 86400),
    "rsize": (4096, 1048576),
    "wsize": (4096, 1048576),
}
OPZIONI_ENUMERATE: dict[str, frozenset[str]] = {
    "proto": frozenset({"tcp", "udp"}),
    "vers": frozenset(VERSIONI_NFS),
    "sec": frozenset({"sys", "krb5", "krb5i", "krb5p"}),
}


def _errore(messaggio: str) -> ErroreAgent:
    return ErroreAgent(CodiceErrore.VALIDAZIONE, messaggio)


def valida_slug(valore: object) -> str:
    if not isinstance(valore, str) or not _SLUG.match(valore):
        raise _errore(
            "Identificatore non valido: sono ammesse solo lettere minuscole, "
            "cifre e trattini, da 1 a 63 caratteri, e non puo iniziare con un trattino."
        )
    return valore


def valida_server(valore: object) -> str:
    """Accetta un indirizzo IP o un nome host."""
    if not isinstance(valore, str) or not valore:
        raise _errore("Indirizzo del server mancante.")
    try:
        ipaddress.ip_address(valore)
    except ValueError:
        if not _HOSTNAME.match(valore):
            raise _errore(f"Indirizzo del server non valido: {valore!r}") from None
    return valore


def valida_percorso_export(valore: object) -> str:
    """Percorso esportato dal NAS: assoluto, normalizzato, senza risalite."""
    if not isinstance(valore, str) or not valore.startswith("/"):
        raise _errore("Il percorso esportato deve essere assoluto.")
    if "\x00" in valore:
        raise _errore("Il percorso contiene caratteri non ammessi.")

    percorso = PurePosixPath(valore)
    if any(parte == ".." for parte in percorso.parts):
        raise _errore("Il percorso esportato non puo contenere '..'.")

    normalizzato = str(PurePosixPath(*[p for p in percorso.parts if p != "."]))
    if not normalizzato.startswith("/"):
        raise _errore("Il percorso esportato deve essere assoluto.")
    return normalizzato.rstrip("/") or "/"


def mountpoint_per(slug: str, radice: PurePosixPath) -> PurePosixPath:
    """Costruisce il punto di montaggio, che e SEMPRE dentro la radice.

    Il percorso non viene mai preso dall'API: si ricava dallo slug gia
    validato. Cosi non esiste alcun modo di far montare qualcosa altrove,
    nemmeno con un input costruito ad arte.
    """
    candidato = radice / valida_slug(slug)
    # Cintura e bretelle: se per qualunque motivo il risultato uscisse dalla
    # radice, ci si ferma qui.
    if not candidato.is_relative_to(radice) or candidato == radice:
        raise _errore("Punto di montaggio fuori dalla radice consentita.")
    return candidato


def valida_versione_nfs(valore: object) -> str:
    if valore is None:
        return "3"
    if not isinstance(valore, str) or valore not in VERSIONI_NFS:
        raise _errore(f"Versione NFS non supportata. Ammesse: {sorted(VERSIONI_NFS)}")
    return valore


def valida_opzioni(opzioni: object) -> list[str]:
    """Filtra le opzioni di mount contro la whitelist.

    Restituisce la lista in forma canonica, pronta per la unit systemd.
    """
    if opzioni is None:
        return []
    if not isinstance(opzioni, list):
        raise _errore("Le opzioni devono essere una lista.")

    risultato: list[str] = []
    viste: set[str] = set()

    for voce in opzioni:
        if not isinstance(voce, str) or not voce:
            raise _errore("Ogni opzione deve essere una stringa non vuota.")

        chiave, _, valore = voce.partition("=")

        if chiave in viste:
            raise _errore(f"Opzione ripetuta: {chiave!r}")
        viste.add(chiave)

        if not valore and chiave in OPZIONI_BOOLEANE:
            risultato.append(chiave)
        elif chiave in OPZIONI_NUMERICHE:
            minimo, massimo = OPZIONI_NUMERICHE[chiave]
            try:
                numero = int(valore)
            except ValueError:
                raise _errore(f"L'opzione {chiave!r} richiede un numero.") from None
            if not minimo <= numero <= massimo:
                raise _errore(f"L'opzione {chiave!r} deve stare fra {minimo} e {massimo}.")
            risultato.append(f"{chiave}={numero}")
        elif chiave in OPZIONI_ENUMERATE:
            ammessi = OPZIONI_ENUMERATE[chiave]
            if valore not in ammessi:
                raise _errore(f"Valore non ammesso per {chiave!r}. Ammessi: {sorted(ammessi)}")
            risultato.append(f"{chiave}={valore}")
        else:
            raise _errore(f"Opzione non consentita: {chiave!r}")

    if "ro" in viste and "rw" in viste:
        raise _errore("Non si possono richiedere insieme sola lettura e scrittura.")

    return risultato


#: Web server gestibili dal pannello.
WEBSERVER = frozenset({"apache", "nginx"})


def valida_hostname(valore: object) -> str:
    """Nome host di un vhost.

    Finisce nel nome del file di configurazione oltre che nel suo contenuto:
    accettare qui una barra o uno spazio significherebbe far scrivere all'agent
    un file dove non deve.
    """
    if not isinstance(valore, str) or not _HOSTNAME.match(valore.strip()):
        raise _errore("Nome host non valido.")
    return valore.strip().lower()


def valida_webserver(valore: object) -> str:
    if not isinstance(valore, str) or valore not in WEBSERVER:
        raise _errore(f"Web server non supportato. Ammessi: {sorted(WEBSERVER)}")
    return valore


def valida_prefisso_url(valore: object) -> str:
    """Prefisso di percorso sotto cui il pannello risponde.

    Restituito sempre nella forma `/qualcosa/`, cioe con barra iniziale e
    finale: e la forma che sia Apache sia Nginx si aspettano, e normalizzarla
    qui evita di dover ricordare la regola in ogni modello.
    """
    if valore is None or valore == "":
        return "/"
    if not isinstance(valore, str):
        raise _errore("Prefisso non valido.")

    pezzi = [p for p in valore.split("/") if p not in ("", ".")]
    if any(p == ".." for p in pezzi):
        raise _errore("Il prefisso non puo contenere '..'.")
    if not all(re.fullmatch(r"[A-Za-z0-9._-]{1,64}", p) for p in pezzi):
        raise _errore("Il prefisso puo contenere solo lettere, cifre, punto, trattino e _.")

    return "/" + "".join(f"{p}/" for p in pezzi)


def valida_porta(valore: object) -> int:
    """Porta su cui gira l'API, verso cui il web server inoltra le richieste."""
    if isinstance(valore, bool) or not isinstance(valore, int):
        raise _errore("Porta non valida.")
    if not 1 <= valore <= 65535:
        raise _errore("Porta fuori intervallo.")
    return valore


def valida_cartella_assoluta(valore: object, *, nome: str) -> PurePosixPath:
    """Percorso assoluto e senza risalite, da mettere in una configurazione.

    Non si verifica che esista: la cartella del pannello puo essere creata
    dopo. Si verifica che sia una forma che non possa uscire dal contesto in
    cui verra scritta.
    """
    if not isinstance(valore, str) or not valore.startswith("/"):
        raise _errore(f"{nome}: serve un percorso assoluto.")
    percorso = PurePosixPath(valore)
    if any(parte == ".." for parte in percorso.parts):
        raise _errore(f"{nome}: il percorso non puo contenere '..'.")
    if any(c in valore for c in "\n\r\x00\"'\\"):
        # Questi caratteri chiuderebbero una direttiva e ne aprirebbero
        # un'altra: e il modo in cui una configurazione generata diventa
        # esecuzione di codice altrui.
        raise _errore(f"{nome}: il percorso contiene caratteri non ammessi.")
    return PurePosixPath(str(percorso).rstrip("/") or "/")
