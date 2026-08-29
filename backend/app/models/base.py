"""Base dichiarativa e colonne comuni a tutte le tabelle."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base di tutti i modelli. Alembic legge da qui i metadati."""


def adesso() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    """Traccia creazione e ultima modifica.

    Le date sono salvate con fuso orario: un pannello che mostra orari sbagliati
    dopo il cambio di ora legale e un difetto che si scopre sei mesi dopo.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=adesso, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=adesso, onupdate=adesso, nullable=False
    )
