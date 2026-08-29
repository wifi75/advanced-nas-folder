"""Schemi dei mount NFS."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AccessoNFS, StatoMount

SLUG = r"^[a-z0-9][a-z0-9-]{0,62}$"


class MountCreate(BaseModel):
    slug: str = Field(pattern=SLUG, description="Identificatore: minuscole, cifre, trattini")
    label: str = Field(min_length=1, max_length=128)
    server: str = Field(min_length=1, max_length=255)
    export_path: str = Field(min_length=1, max_length=1024)
    nfs_version: str = Field(default="3", pattern=r"^(3|4\.0|4\.1|4\.2)$")
    automount: bool = True
    idle_timeout: int = Field(default=600, ge=0, le=86400)
    #: Volutamente falso per impostazione predefinita: la scrittura si abilita
    #: con un gesto esplicito, non per distrazione.
    consenti_scrittura: bool = False


class MountUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=128)
    nfs_version: str | None = Field(default=None, pattern=r"^(3|4\.0|4\.1|4\.2)$")
    automount: bool | None = None
    idle_timeout: int | None = Field(default=None, ge=0, le=86400)
    consenti_scrittura: bool | None = None


class StatoEffettivo(BaseModel):
    """Cio che il sistema riporta davvero, non cio che e stato chiesto."""

    montato: bool = False
    sorgente: str | None = None
    opzioni: str | None = None
    scrittura: bool | None = None
    #: Esito della prova di scrittura sul campo. Piu attendibile delle opzioni:
    #: il NAS puo negare la scrittura anche a un mount richiesto in lettura-scrittura.
    scrittura_verificata: bool | None = None


class MountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    label: str
    server: str
    export_path: str
    mountpoint: str
    nfs_version: str
    requested_access: AccessoNFS
    automount: bool
    idle_timeout: int
    state: StatoMount
    effective_read_write: bool | None
    effective_options: str | None
    last_error: str | None

    @property
    def scrittura_negata_dal_nas(self) -> bool:
        return (
            self.requested_access is AccessoNFS.LETTURA_SCRITTURA
            and self.effective_read_write is False
        )


class MountDettaglio(MountOut):
    """Mount con lo stato riletto dal sistema al momento della richiesta."""

    effettivo: StatoEffettivo | None = None
    #: Valorizzato quando si e chiesta la scrittura ma il NAS la nega: e la
    #: condizione che va mostrata in evidenza nel pannello.
    avviso: str | None = None


class Esportazione(BaseModel):
    percorso: str
    client: str


class ScopertaRichiesta(BaseModel):
    server: str = Field(min_length=1, max_length=255)


class ScopertaRisposta(BaseModel):
    server: str
    esportazioni: list[Esportazione]
    #: Versioni NFS che il NAS espone davvero. Se manca la 4, chiedere NFSv4
    #: fallisce con "Protocol not supported".
    versioni: list[str]


class MontaggioPreesistente(BaseModel):
    """Un montaggio NFS trovato in /etc/fstab, non ancora gestito dal pannello."""

    riga: int
    server: str
    export: str
    mountpoint: str
    tipo: str
    opzioni: str
    #: Identificatore proposto, ricavato dal percorso di montaggio.
    slug_proposto: str
    #: Vero se il pannello gestisce già una condivisione con quello stesso NAS
    #: e percorso: importarla di nuovo creerebbe un doppione.
    gia_gestito: bool = False


class DisattivaFstab(BaseModel):
    mountpoint: str = Field(min_length=1, max_length=1024, pattern=r"^/.*")
