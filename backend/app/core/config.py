"""Configurazione dell'applicazione, letta da ambiente e da .env.

Nessun valore reale dell'impianto vive nel codice: tutto arriva da qui.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

#: Dove cercare il file `.env`, in percorsi **assoluti**.
#:
#: Un percorso relativo verrebbe risolto dalla cartella corrente, che non è la
#: stessa per tutti: l'applicazione gira da `backend/`, alembic anche, ma in
#: produzione il file sta nella radice dell'installazione. Cercarlo lì e basta
#: faceva fallire le migrazioni con «secret_key: Field required», senza che il
#: messaggio lasciasse capire che era un problema di percorso.
#:
#: L'ordine conta: pydantic legge i file in sequenza e gli ultimi vincono.
_BACKEND = Path(__file__).resolve().parents[2]
_RADICE = _BACKEND.parent
_FILE_ENV = (_RADICE / ".env", _BACKEND / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ANF_",
        env_file=_FILE_ENV,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Applicazione ---
    env: Literal["development", "production"] = "production"
    host: str = "127.0.0.1"
    port: int = 8100
    base_url: str = "http://localhost:8100"
    log_level: str = "INFO"

    # --- Sicurezza ---
    secret_key: str = Field(min_length=32)
    access_token_minutes: int = 30
    refresh_token_days: int = 14

    # --- Database ---
    db_path: Path = Path("/var/lib/anf/anf.sqlite3")
    db_wal: bool = True

    # --- Agent privilegiato ---
    agent_socket: Path = Path("/run/anf/agent.sock")
    mount_root: Path = Path("/srv/nas")

    #: Cartella in cui l'installer mette i file compilati del pannello. Serve
    #: alla configurazione del web server, che deve sapere cosa servire.
    panel_dir: Path = Path("/var/www/anf/pannello")

    # --- Consegna dei download ---
    #: In sviluppo diventa "stream" da solo: senza un web server davanti,
    #: "xsendfile" produce risposte vuote che sembrano un difetto del codice.
    download_backend: Literal["xsendfile", "xaccel", "stream"] = "xsendfile"
    xaccel_prefix: str = "/__anf_internal"

    # --- Monitoraggio ---
    access_log: Path | None = None
    trusted_proxies: str = "127.0.0.1"

    @field_validator("mount_root", "agent_socket", "db_path", "panel_dir")
    @classmethod
    def _deve_essere_assoluto(cls, v: Path) -> Path:
        # I valori predefiniti sono percorsi Linux, dove il progetto gira. Su
        # Windows, dove lo si sviluppa, `is_absolute()` li considera relativi:
        # senza questa seconda condizione l'applicazione non partirebbe li
        # nemmeno per guardarla.
        if not v.is_absolute() and not str(v).replace("\\", "/").startswith("/"):
            raise ValueError(f"{v} deve essere un percorso assoluto")
        return v

    @model_validator(mode="after")
    def _consegna_adatta_allambiente(self) -> Settings:
        if self.env == "development" and "download_backend" not in self.model_fields_set:
            object.__setattr__(self, "download_backend", "stream")
        return self

    @property
    def cartella_miniature(self) -> Path:
        """Dove finiscono le miniature generate.

        Accanto al database e non dentro il mount: le miniature sono roba
        nostra, e scriverle sul NAS significherebbe sporcare le cartelle di chi
        le ha condivise — oltre a richiedere il permesso di scrittura, che di
        norma non c'e'.
        """
        return self.db_path.parent / "miniature"

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path}"

    @property
    def trusted_proxy_list(self) -> list[str]:
        return [p.strip() for p in self.trusted_proxies.split(",") if p.strip()]

    @property
    def is_dev(self) -> bool:
        return self.env == "development"


@lru_cache
def get_settings() -> Settings:
    """Istanza unica, memorizzata: la configurazione si legge una volta sola."""
    return Settings()  # type: ignore[call-arg]
