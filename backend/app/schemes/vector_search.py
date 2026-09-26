# app/schemes/vector_search.py

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embedding_service import get_embedding_provider
from app.schemes.document_models import DocumentChunk


async def search_chunks(
    db: AsyncSession,
    query_text: str,
    candidate_scheme_ids: list[uuid.UUID],
    top_k: int = 10,
) -> list[tuple[DocumentChunk, float]]:
    """
    Embeds query_text and finds the most semantically similar chunks,
    restricted to candidate_scheme_ids (the output of metadata filtering).
    Returns (chunk, cosine_distance) pairs, ordered most-similar first.
    Lower distance = more similar; 0 = identical, 2 = maximally dissimilar.
    """
    if not candidate_scheme_ids:
        return []

    provider = get_embedding_provider()
    query_embedding = provider.embed_text(query_text)

    distance = DocumentChunk.embedding.cosine_distance(query_embedding)

    result = await db.execute(
        select(DocumentChunk, distance.label("distance"))
        .where(DocumentChunk.scheme_id.in_(candidate_scheme_ids))
        .order_by(distance)
        .limit(top_k)
    )

    return [(row[0], row[1]) for row in result.all()]