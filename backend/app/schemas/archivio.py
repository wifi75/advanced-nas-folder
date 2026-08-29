"""Schemi della consultazione delle cartelle pubblicate."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    StatoTrasferimento,
    TipoTrasferimento,
    Visibilita,
    WebServer,
)


class VoceOut(BaseModel):
    nome: str
    percorso: str
    cartella: bool
    #: Assente per le cartelle: calcolarne la dimensione richiederebbe di
    #: percorrerle tutte, cosa che su NFS costa quanto l'elenco stesso.
    dimensione: int | None = None
    modificato: datetime | None = None


class ContenutoOut(BaseModel):
    slug: str
    label: str
    descrizione: str | None = None
    percorso: str
    #: Nome e percorso di ogni cartella attraversata, per tornare indietro.
    briciole: list[tuple[str, str]] = []
    voci: list[VoceOut] = []
    scrittura: bool = False
    visibilita: Visibilita


class RichiestaGettone(BaseModel):
    percorso: str = Field(default="", max_length=1024)
    #: Necessaria solo se il percorso e' protetto da password.
    password: str | None = Field(default=None, max_length=256)


class GettoneOut(BaseModel):
    """Autorizzazione a vita breve da mettere nel collegamento di download."""

    gettone: str
    valido_secondi: int


class LinkCreate(BaseModel):
    """Un nuovo link di condivisione.

    Tutti i limiti sono facoltativi: un link senza scadenza né limite è una
    scelta legittima, purché sia una scelta.
    """

    percorso: str = Field(default="", max_length=1024)
    etichetta: str | None = Field(default=None, max_length=128)
    #: Protezione aggiuntiva: chi ha il collegamento deve anche saperla.
    password: str | None = Field(default=None, min_length=1, max_length=256)
    #: Durata in giorni. Assente = nessuna scadenza.
    giorni: int | None = Field(default=None, ge=1, le=3650)
    #: Numero massimo di scaricamenti. Assente = nessun limite.
    max_download: int | None = Field(default=None, ge=1)


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    path: str
    label: str | None
    expires_at: datetime | None
    max_downloads: int | None
    download_count: int
    is_revoked: bool
    protetto_da_password: bool = False
    #: Vero se il link non apre più nulla: scaduto, revocato o esaurito.
    esaurito: bool = False


class LinkCreato(LinkOut):
    """Il link appena creato, con il token in chiaro.

    È l'unico momento in cui il token esiste fuori dal database, che ne
    conserva solo l'impronta: dopo non è più recuperabile.
    """

    token: str


class VHostCreate(BaseModel):
    """Pubblicazione del pannello su un nome host del web server."""

    hostname: str = Field(min_length=1, max_length=255)
    webserver: WebServer
    #: Prefisso sotto cui il pannello risponde. `/` = radice del sito.
    prefisso: str = Field(default="/", max_length=255)
    share_id: int | None = None


class VHostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hostname: str
    path_prefix: str
    webserver: WebServer
    is_enabled: bool
    share_id: int | None
    last_error: str | None


class VHostAnteprima(BaseModel):
    """Cio che verrebbe scritto, prima di scriverlo davvero."""

    configurazione: str


class WebServerDisponibili(BaseModel):
    installati: list[WebServer]


class CreaCartella(BaseModel):
    #: Cartella in cui creare. Vuoto = radice della pubblicazione.
    percorso: str = Field(default="", max_length=1024)
    nome: str = Field(min_length=1, max_length=255)


class Rinomina(BaseModel):
    percorso: str = Field(min_length=1, max_length=1024)
    nome: str = Field(min_length=1, max_length=255)


class Trasferisci(BaseModel):
    """Spostamento o copia di un elemento in un'altra cartella."""

    percorso: str = Field(min_length=1, max_length=1024)
    #: Cartella di destinazione. Vuoto = radice della pubblicazione.
    destinazione: str = Field(default="", max_length=1024)
    #: Solo per la copia: nome diverso, se serve.
    nome: str | None = Field(default=None, min_length=1, max_length=255)


class Elimina(BaseModel):
    percorso: str = Field(min_length=1, max_length=1024)
    #: Necessario per eliminare una cartella che contiene qualcosa.
    ricorsivo: bool = False


class StatoCaricamento(BaseModel):
    """Da dove riprendere un caricamento interrotto."""

    nome: str
    #: Byte già arrivati. Zero significa che si parte dall'inizio.
    ricevuti: int
    #: Vero se esiste già un file con quel nome: completare fallirebbe.
    gia_presente: bool


class CompletaCaricamento(BaseModel):
    percorso: str = Field(default="", max_length=1024)
    nome: str = Field(min_length=1, max_length=255)
    #: Dimensione totale attesa. Serve a non completare un file troncato.
    dimensione: int | None = Field(default=None, ge=0)


class RisultatiRicerca(BaseModel):
    termine: str
    percorso: str
    voci: list[VoceOut] = []
    #: Vero se la ricerca si è fermata a un limite: l'elenco non è completo.
    troncata: bool = False


class SelezioneZip(BaseModel):
    """Elementi scelti a mano da mettere in un unico archivio."""

    percorsi: list[str] = Field(min_length=1, max_length=500)
    #: Nome proposto per il file scaricato.
    nome: str = Field(default="selezione", max_length=128)


class RichiestaChecksum(BaseModel):
    percorso: str = Field(min_length=1, max_length=1024)


class Checksum(BaseModel):
    percorso: str
    algoritmo: str = "sha256"
    valore: str
    dimensione: int


class TrasferimentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: TipoTrasferimento
    status: StatoTrasferimento
    share_id: int | None
    user_id: int | None
    path: str
    size: int | None
    #: Byte davvero arrivati. Resta vuoto finché il web server non li ha
    #: scritti nel suo log: un numero inventato sarebbe peggio di uno assente.
    bytes_transferred: int | None
    client_ip: str | None
    is_resumed: bool
    started_at: datetime
    finished_at: datetime | None
