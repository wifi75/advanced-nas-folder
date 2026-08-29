"""Modelli del database.

Importati tutti qui: Alembic rileva le tabelle solo se le classi sono state
caricate quando legge `Base.metadata`.
"""

from app.models.base import Base
from app.models.enums import (
    AccessoNFS,
    Livello,
    StatoMount,
    StatoTrasferimento,
    TipoTrasferimento,
    Visibilita,
    WebServer,
)
from app.models.mount import Mount
from app.models.share import AccessRule, PermessoUtente, Share, ShareLink
from app.models.system import Setting, Transfer, VHost
from app.models.user import User

__all__ = [
    "AccessRule",
    "AccessoNFS",
    "Base",
    "Livello",
    "Mount",
    "PermessoUtente",
    "Setting",
    "Share",
    "ShareLink",
    "StatoMount",
    "StatoTrasferimento",
    "TipoTrasferimento",
    "Transfer",
    "User",
    "VHost",
    "Visibilita",
    "WebServer",
]
