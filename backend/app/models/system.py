"""Trasferimenti monitorati, pubblicazioni sul web server, impostazioni."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import StatoTrasferimento, TipoTrasferimento, WebServer


class Transfer(Base):
    """Un download o un upload, per la dashboard di monitoraggio.

    I byte trasferiti non li conosce l'applicazione: la consegna e delegata al
    web server. Vengono letti dal suo access log a trasferimento concluso, per
    questo `bytes_transferred` resta nullo finche il trasferimento e in corso.
    """

    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[TipoTrasferimento] = mapped_column(Enum(TipoTrasferimento, native_enum=False))
    status: Mapped[StatoTrasferimento] = mapped_column(
        Enum(StatoTrasferimento, native_enum=False), default=StatoTrasferimento.IN_CORSO
    )

    share_id: Mapped[int | None] = mapped_column(
        ForeignKey("shares.id", ondelete="SET NULL"), default=None
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    share_link_id: Mapped[int | None] = mapped_column(
        ForeignKey("share_links.id", ondelete="SET NULL"), default=None
    )

    path: Mapped[str] = mapped_column(String(1024))
    size: Mapped[int | None] = mapped_column(default=None)
    bytes_transferred: Mapped[int | None] = mapped_column(default=None)

    #: Indirizzo reale del client. Dietro un reverse proxy richiede
    #: mod_remoteip e X-Forwarded-For, altrimenti qui finisce l'IP del proxy e
    #: il monitoraggio non distingue nessuno.
    client_ip: Mapped[str | None] = mapped_column(String(64), default=None)
    user_agent: Mapped[str | None] = mapped_column(Text, default=None)
    #: Vero se la richiesta usava Range, cioe se e la ripresa di un download.
    is_resumed: Mapped[bool] = mapped_column(Boolean, default=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    def __repr__(self) -> str:
        return f"<Transfer {self.kind} {self.path!r} {self.status}>"


class VHost(Base, TimestampMixin):
    """Pubblicazione di uno share su un hostname del web server.

    L'applicazione genera solo la configurazione locale: DNS e certificati
    vivono altrove, tipicamente su un reverse proxy a monte.
    """

    __tablename__ = "vhosts"

    id: Mapped[int] = mapped_column(primary_key=True)
    hostname: Mapped[str] = mapped_column(String(255), index=True)
    path_prefix: Mapped[str] = mapped_column(String(255), default="/")
    share_id: Mapped[int] = mapped_column(ForeignKey("shares.id", ondelete="CASCADE"))

    webserver: Mapped[WebServer] = mapped_column(Enum(WebServer, native_enum=False))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    #: Configurazione realmente scritta, conservata per poter ripristinare la
    #: versione precedente se il test di sintassi fallisce.
    rendered_config: Mapped[str | None] = mapped_column(Text, default=None)
    last_error: Mapped[str | None] = mapped_column(Text, default=None)

    def __repr__(self) -> str:
        return f"<VHost {self.hostname}{self.path_prefix}>"


class Setting(Base, TimestampMixin):
    """Impostazioni modificabili dal pannello.

    Stanno nel database e non in un file: l'amministratore le cambia
    dall'interfaccia, che e il requisito di partenza del progetto.
    """

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    def __repr__(self) -> str:
        return f"<Setting {self.key!r}>"
