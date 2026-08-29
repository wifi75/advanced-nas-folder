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
