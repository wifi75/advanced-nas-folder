"""Schemi della consultazione delle cartelle pubblicate."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Visibilita


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
