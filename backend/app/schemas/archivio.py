"""Schemi della consultazione delle cartelle pubblicate."""

from datetime import datetime

from pydantic import BaseModel, Field

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
