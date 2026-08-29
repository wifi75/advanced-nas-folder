"""Motore, sessioni e impostazioni di SQLite.

SQLite regge bene questo carico (pochi utenti, scritture rare, letture frequenti)
ma **solo** con la modalita WAL: senza, ogni scrittura bloccherebbe le letture e il
pannello si inchioderebbe a ogni salvataggio.
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


def _applica_pragma(dbapi_connection: Any, _record: Any) -> None:
    """Impostazioni applicate a ogni nuova connessione SQLite.

    SQLite le dimentica a ogni connessione (tranne journal_mode, che e
    persistente), quindi vanno riapplicate qui e non una volta sola all'avvio.
    """
    settings = get_settings()
    cursor = dbapi_connection.cursor()
    if settings.db_wal:
        # Letture concorrenti durante una scrittura. Persistente sul file.
        cursor.execute("PRAGMA journal_mode=WAL")
    # Compromesso durabilita/velocita corretto in abbinamento a WAL.
    cursor.execute("PRAGMA synchronous=NORMAL")
    # Senza questo SQLite ignora le chiavi esterne, in silenzio.
    cursor.execute("PRAGMA foreign_keys=ON")
    # Attende invece di fallire subito se il file e occupato (millisecondi).
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def crea_engine() -> AsyncEngine:
    settings = get_settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_async_engine(
        settings.database_url,
        echo=settings.is_dev,
        future=True,
    )
    event.listen(engine.sync_engine, "connect", _applica_pragma)
    return engine


engine: AsyncEngine = crea_engine()

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Dipendenza FastAPI: una sessione per richiesta, chiusa in ogni caso."""
    async with SessionLocal() as session:
        yield session
