"""propone i nomi nascosti alle pubblicazioni gia esistenti

Revision ID: 25728398166b
Revises: b06a5b403a9c
Create Date: 2026-08-30 15:17:56.997370
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "25728398166b"
down_revision: str | None = "b06a5b403a9c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Riempie l'elenco solo dove e' rimasto vuoto.

    La migrazione precedente aveva aggiunto la colonna con valore vuoto, quindi
    le pubblicazioni create prima di questa funzione continuavano a mostrare il
    cestino del NAS: la proposta valeva solo per le nuove, che e' esattamente
    il contrario di quello che serve a chi aggiorna.

    Tocca solo le righe vuote. Chi ha gia' scelto cosa nascondere — anche
    scegliendo di non nascondere niente, nella breve finestra fra le due
    versioni — se lo vede sovrascritto; e' il prezzo di sistemare un valore
    predefinito dopo averlo rilasciato, e riguarda un elenco che si rimodifica
    in un istante.
    """
    proposti = "\n".join(
        ("#recycle", "#snapshot", "@eaDir", ".DS_Store", "Thumbs.db", "$RECYCLE.BIN")
    )
    op.execute(
        sa.text(
            "UPDATE shares SET hidden_patterns = :proposti WHERE hidden_patterns = ''"
        ).bindparams(proposti=proposti)
    )


def downgrade() -> None:
    """Non si torna indietro: non si sa quali righe erano vuote per scelta."""
