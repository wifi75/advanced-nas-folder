"""Ambiente delle migrazioni Alembic.

L'URL del database arriva dalla configurazione dell'applicazione, non da
alembic.ini: una sola sorgente di verita, e nessun percorso reale nel
repository.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)

target_metadata = Base.metadata


def _opzioni_comuni() -> dict[str, object]:
    return {
        "target_metadata": target_metadata,
        # SQLite non sa modificare una colonna con ALTER: senza il "batch mode"
        # Alembic non riesce a generare migrazioni che cambiano tipi o vincoli.
        "render_as_batch": True,
        "compare_type": True,
        "compare_server_default": True,
    }


def run_migrations_offline() -> None:
    """Genera l'SQL senza connettersi al database."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_opzioni_comuni(),  # type: ignore[arg-type]
    )
    with context.begin_transaction():
        context.run_migrations()


def _esegui(connection: Connection) -> None:
    context.configure(connection=connection, **_opzioni_comuni())  # type: ignore[arg-type]
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with engine.connect() as connection:
        await connection.run_sync(_esegui)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
