"""Cartelle pubblicate, regole di accesso e link di condivisione."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import Livello, Visibilita


class Share(Base, TimestampMixin):
    """Una cartella pubblicata, a partire da un mount piu un sottopercorso."""

    __tablename__ = "shares"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, default=None)

    mount_id: Mapped[int] = mapped_column(ForeignKey("mounts.id", ondelete="CASCADE"))
    #: Sottopercorso dentro il mount. Vuoto = radice del mount.
    subpath: Mapped[str] = mapped_column(String(1024), default="")

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    #: Visibilita applicata dove nessuna regola piu specifica corrisponde.
    default_visibility: Mapped[Visibilita] = mapped_column(
        Enum(Visibilita, native_enum=False), default=Visibilita.UTENTI
    )

    # Riferimento in avanti senza virgolette: da Python 3.14 le annotazioni sono
    # valutate in modo differito, e SQLAlchemy le risolve quando configura i
    # mapper, cioe quando AccessRule esiste gia.
    rules: Mapped[list[AccessRule]] = relationship(
        back_populates="share", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Share {self.slug!r}>"


class AccessRule(Base, TimestampMixin):
    """Regola di accesso per un prefisso di percorso dentro uno share.

    Vince la regola con il prefisso piu lungo che corrisponde: e cosi che una
    sottocartella puo essere piu restrittiva della cartella che la contiene.
    """

    __tablename__ = "access_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    share_id: Mapped[int] = mapped_column(ForeignKey("shares.id", ondelete="CASCADE"))

    #: Prefisso normalizzato, senza barra iniziale. Vuoto = tutto lo share.
    path_prefix: Mapped[str] = mapped_column(String(1024), default="")
    visibility: Mapped[Visibilita] = mapped_column(Enum(Visibilita, native_enum=False))
    #: Hash Argon2, valorizzato solo per visibilita "password".
    password_hash: Mapped[str | None] = mapped_column(Text, default=None)

    share: Mapped[Share] = relationship(back_populates="rules")

    def __repr__(self) -> str:
        return f"<AccessRule {self.path_prefix!r} {self.visibility}>"


class PermessoUtente(Base, TimestampMixin):
    """Permesso di un singolo utente su un percorso dentro uno share.

    E cio che permette di dire "questa cartella la vede solo Mario", cosa che
    la sola visibilita del percorso non sa esprimere: quella distingue fra
    chiunque, chi ha la password e chi e autenticato, ma non fra una persona e
    un'altra.

    Come per le regole di visibilita, vince il prefisso piu lungo: si puo
    concedere un ramo intero e togliere una sottocartella al suo interno.
    """

    __tablename__ = "permessi_utente"
    __table_args__ = (
        UniqueConstraint("user_id", "share_id", "path_prefix", name="uq_permesso_percorso"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    share_id: Mapped[int] = mapped_column(ForeignKey("shares.id", ondelete="CASCADE"), index=True)

    #: Prefisso normalizzato, senza barra iniziale. Vuoto = tutto lo share.
    path_prefix: Mapped[str] = mapped_column(String(1024), default="")
    livello: Mapped[Livello] = mapped_column(
        Enum(Livello, native_enum=False), default=Livello.LETTURA
    )

    def __repr__(self) -> str:
        return (
            f"<PermessoUtente u={self.user_id} s={self.share_id} "
            f"{self.path_prefix!r} {self.livello}>"
        )


class ShareLink(Base, TimestampMixin):
    """Link di condivisione con token, scadenza e limite di download."""

    __tablename__ = "share_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    share_id: Mapped[int] = mapped_column(ForeignKey("shares.id", ondelete="CASCADE"))
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )

    #: Solo l'hash del token e memorizzato: chi legge il database non puo
    #: ricostruire i link attivi.
    token_hash: Mapped[str] = mapped_column(Text, unique=True, index=True)
    path: Mapped[str] = mapped_column(String(1024), default="")
    label: Mapped[str | None] = mapped_column(String(128), default=None)

    password_hash: Mapped[str | None] = mapped_column(Text, default=None)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    max_downloads: Mapped[int | None] = mapped_column(default=None)
    download_count: Mapped[int] = mapped_column(default=0)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<ShareLink share={self.share_id} path={self.path!r}>"
