"""Preparazione iniziale del database."""

import logging

from sqlalchemy import func, select

from app.api.v1.auth import PASSWORD_INIZIALE
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import User

logger = logging.getLogger("anf.bootstrap")


async def crea_amministratore_iniziale() -> None:
    """Crea l'utente `admin` se il database non ha ancora nessun utente.

    Serve a rendere il pannello utilizzabile subito dopo l'installazione. La
    password iniziale e volutamente banale ed e segnalata in modo evidente:
    l'API la marca nella risposta di accesso e il pannello mostra un avviso
    finche non viene cambiata.
    """
    async with SessionLocal() as sessione:
        quanti = await sessione.scalar(select(func.count()).select_from(User))
        if quanti:
            return

        admin = User(
            username="admin",
            password_hash=hash_password(PASSWORD_INIZIALE),
            is_admin=True,
            is_active=True,
            can_create=True,
            can_delete=True,
            can_modify=True,
            can_rename=True,
            can_share=True,
            can_download=True,
            can_upload=True,
        )
        sessione.add(admin)
        await sessione.commit()

    logger.warning(
        "Creato l'utente amministratore iniziale 'admin' con password '%s'. "
        "CAMBIALA prima di rendere il pannello raggiungibile da Internet.",
        PASSWORD_INIZIALE,
    )
