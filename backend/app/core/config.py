"""Configurazione dell'applicazione, letta da ambiente e da .env.

Nessun valore reale dell'impianto vive nel codice: tutto arriva da qui.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ANF_",
        env_file=".env",
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

    # --- Consegna dei download ---
    download_backend: Literal["xsendfile", "xaccel", "stream"] = "xsendfile"
    xaccel_prefix: str = "/__anf_internal"

    # --- Monitoraggio ---
    access_log: Path | None = None
    trusted_proxies: str = "127.0.0.1"

    @field_validator("mount_root", "agent_socket", "db_path")
    @classmethod
    def _deve_essere_assoluto(cls, v: Path) -> Path:
        if not v.is_absolute():
            raise ValueError(f"{v} deve essere un percorso assoluto")
        return v

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
