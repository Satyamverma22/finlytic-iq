"""add ivfflat index on document_chunks embedding

Revision ID: 0f11384952db
Revises: 0fff19349b26
Create Date: 2026-09-24 12:19:28.953938

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f11384952db'
down_revision: Union[str, None] = '0fff19349b26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX ix_document_chunks_embedding_cosine
        ON document_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 10)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX ix_document_chunks_embedding_cosine")
