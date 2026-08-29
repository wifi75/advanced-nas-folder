"""Condivisioni NFS gestite dal pannello."""

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import AccessoNFS, StatoMount


class Mount(Base, TimestampMixin):
    """Una condivisione NFS, con lo stato richiesto e quello reale.

    La distinzione fra i due non e un dettaglio: il pannello puo *chiedere* la
    scrittura, ma se la regola NFS sul NAS e in sola lettura il mount resta in
    sola lettura. Registrare solo l'intenzione significherebbe mostrare
    all'utente uno stato falso.
    """

    __tablename__ = "mounts"

    id: Mapped[int] = mapped_column(primary_key=True)

    #: Identificatore usato nel nome della unit systemd e nel mountpoint.
    #: Vincolato a [a-z0-9-]+ dai validatori dell'agent.
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(128))

    server: Mapped[str] = mapped_column(String(255))
    export_path: Mapped[str] = mapped_column(String(1024))
    #: Sempre sotto ANF_MOUNT_ROOT. Imposto dall'agent, non dall'utente.
    mountpoint: Mapped[str] = mapped_column(String(1024), unique=True)

    nfs_version: Mapped[str] = mapped_column(String(8), default="3")

    # --- Richiesto ---
    requested_access: Mapped[AccessoNFS] = mapped_column(
        Enum(AccessoNFS, native_enum=False), default=AccessoNFS.SOLA_LETTURA
    )
    automount: Mapped[bool] = mapped_column(Boolean, default=True)
    idle_timeout: Mapped[int] = mapped_column(default=600)

    # --- Effettivo, riletto dal sistema dopo ogni operazione ---
    state: Mapped[StatoMount] = mapped_column(
        Enum(StatoMount, native_enum=False), default=StatoMount.CONFIGURATO
    )
    effective_read_write: Mapped[bool | None] = mapped_column(Boolean, default=None)
    effective_options: Mapped[str | None] = mapped_column(Text, default=None)
    last_error: Mapped[str | None] = mapped_column(Text, default=None)

    @property
    def scrittura_negata_dal_nas(self) -> bool:
        """Vero se abbiamo chiesto la scrittura e il NAS l'ha rifiutata.

        E la condizione da mostrare in evidenza nel pannello: senza, l'utente
        crede di poter caricare file e scopre il contrario al primo upload.
        """
        return (
            self.requested_access is AccessoNFS.LETTURA_SCRITTURA
            and self.effective_read_write is False
        )

    def __repr__(self) -> str:
        return f"<Mount {self.slug!r} {self.server}:{self.export_path} {self.state}>"
