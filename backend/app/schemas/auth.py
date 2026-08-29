"""Schemi di richiesta e risposta per l'autenticazione."""

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    is_admin: bool
    locale: str
    theme: str
    hide_dotfiles: bool
    can_create: bool
    can_delete: bool
    can_modify: bool
    can_rename: bool
    can_share: bool
    can_download: bool
    can_upload: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - schema OAuth2, non una password
    expires_in: int
    user: UserOut
    #: Vero se l'utente sta ancora usando la password iniziale. Il pannello
    #: mostra un avviso finche non viene cambiata.
    password_predefinita: bool = False


class UserAdminOut(UserOut):
    """L'utente come lo vede l'amministratore.

    Aggiunge i campi che servono a gestirlo ma che non interessano a chi
    guarda il proprio profilo.
    """

    is_active: bool
    scope: str


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    #: Lunghezza minima alta di proposito: e' l'unica difesa di un pannello
    #: che espone cartelle di rete, e una password corta la annulla.
    password: str = Field(min_length=10, max_length=256)
    email: str | None = Field(default=None, max_length=255)
    is_admin: bool = False
    #: Percorso oltre il quale l'utente non puo' uscire. Vuoto = nessun limite.
    scope: str = Field(default="", max_length=1024)
    can_create: bool = False
    can_delete: bool = False
    can_modify: bool = False
    can_rename: bool = False
    can_share: bool = False
    can_download: bool = True
    can_upload: bool = False


class UserUpdate(BaseModel):
    """Modifica di un utente. I campi assenti restano come sono."""

    password: str | None = Field(default=None, min_length=10, max_length=256)
    email: str | None = Field(default=None, max_length=255)
    is_admin: bool | None = None
    is_active: bool | None = None
    scope: str | None = Field(default=None, max_length=1024)
    can_create: bool | None = None
    can_delete: bool | None = None
    can_modify: bool | None = None
    can_rename: bool | None = None
    can_share: bool | None = None
    can_download: bool | None = None
    can_upload: bool | None = None


class CambioPassword(BaseModel):
    """Cambio della propria password."""

    attuale: str = Field(min_length=1, max_length=256)
    nuova: str = Field(min_length=10, max_length=256)
