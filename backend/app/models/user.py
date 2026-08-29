"""Utenti e permessi."""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, default=None)

    #: Hash Argon2. La password in chiaro non esiste in nessun punto del sistema.
    password_hash: Mapped[str] = mapped_column(Text)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    #: Percorso oltre il quale l'utente non puo uscire, relativo allo share.
    #: Vuoto = nessuna restrizione. Verificato dopo la normalizzazione del
    #: percorso, mai per confronto di stringhe grezze.
    scope: Mapped[str] = mapped_column(String(1024), default="")

    # Permessi granulari, sul modello di FileBrowser.
    can_create: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    can_modify: Mapped[bool] = mapped_column(Boolean, default=False)
    can_rename: Mapped[bool] = mapped_column(Boolean, default=False)
    can_share: Mapped[bool] = mapped_column(Boolean, default=False)
    can_download: Mapped[bool] = mapped_column(Boolean, default=True)
    can_upload: Mapped[bool] = mapped_column(Boolean, default=False)

    locale: Mapped[str] = mapped_column(String(8), default="it")
    theme: Mapped[str] = mapped_column(String(16), default="auto")
    hide_dotfiles: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<User {self.username!r} admin={self.is_admin}>"
