"""Schemi delle cartelle pubblicate, delle regole e dei permessi."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import Livello, Visibilita

SLUG = r"^[a-z0-9][a-z0-9-]{0,62}$"


class ShareCreate(BaseModel):
    slug: str = Field(pattern=SLUG)
    label: str = Field(min_length=1, max_length=128)
    mount_id: int
    #: Sottopercorso dentro il mount. Vuoto = radice del mount.
    subpath: str = Field(default="", max_length=1024)
    description: str | None = None
    default_visibility: Visibilita = Visibilita.UTENTI
    is_enabled: bool = True


class ShareUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    default_visibility: Visibilita | None = None
    is_enabled: bool | None = None


class RegolaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    path_prefix: str
    visibility: Visibilita
    #: Non si restituisce mai l'hash: solo se una password è impostata.
    protetta_da_password: bool = False


class RegolaCreate(BaseModel):
    path_prefix: str = Field(default="", max_length=1024)
    visibility: Visibilita
    #: Obbligatoria per la visibilità "password", ignorata altrove.
    password: str | None = Field(default=None, min_length=1, max_length=256)

    @model_validator(mode="after")
    def _password_dove_serve(self) -> RegolaCreate:
        if self.visibility is Visibilita.PASSWORD and not self.password:
            raise ValueError("La visibilità 'password' richiede una password.")
        return self


class PermessoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    path_prefix: str
    livello: Livello


class PermessoCreate(BaseModel):
    user_id: int
    path_prefix: str = Field(default="", max_length=1024)
    livello: Livello = Livello.LETTURA


class ShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    label: str
    description: str | None
    mount_id: int
    subpath: str
    is_enabled: bool
    default_visibility: Visibilita


class ShareDettaglio(ShareOut):
    regole: list[RegolaOut] = []
    permessi: list[PermessoOut] = []


class ProvaAccesso(BaseModel):
    """Richiesta per capire *perché* un percorso è o non è accessibile.

    Serve a chi configura i permessi: senza, l'unico modo di verificarli è
    provare con l'utente vero e indovinare quale regola ha deciso.
    """

    percorso: str = Field(default="", max_length=1024)
    user_id: int | None = None


class EsitoAccesso(BaseModel):
    consentito: bool
    scrittura: bool
    visibilita: Visibilita
    motivo: str
    #: Prefisso della regola che ha deciso, se ce n'è una.
    regola: str | None = None
    #: Prefisso del permesso personale che ha deciso, se ce n'è uno.
    permesso: str | None = None
