"""nomi da nascondere per pubblicazione

Revision ID: b06a5b403a9c
Revises: 7bd9aecd96f7
Create Date: 2026-08-30 15:12:25.214523
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b06a5b403a9c"
down_revision: str | None = "7bd9aecd96f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # `server_default` non e' decorativo: senza, la colonna non ammette NULL e
    # le pubblicazioni gia' esistenti non avrebbero un valore, quindi la
    # migrazione fallirebbe sul primo database non vuoto.
    with op.batch_alter_table("shares", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("hidden_patterns", sa.Text(), nullable=False, server_default="")
        )


def downgrade() -> None:
    with op.batch_alter_table("shares", schema=None) as batch_op:
        batch_op.drop_column("hidden_patterns")
