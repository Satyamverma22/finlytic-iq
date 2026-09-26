# app/schemes/embedding_pipeline.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embedding_service import get_embedding_provider
from app.schemes.document_models import DocumentChunk


async def embed_pending_chunks(db: AsyncSession) -> int:
    """
    Finds every DocumentChunk with embedding IS NULL, embeds their
    content in one batch call, and stores the vectors back.
    Returns the number of chunks embedded.
    """
    result = await db.execute(
        select(DocumentChunk).where(DocumentChunk.embedding.is_(None))
    )
    pending_chunks = list(result.scalars().all())

    if not pending_chunks:
        return 0

    provider = get_embedding_provider()
    texts = [chunk.content for chunk in pending_chunks]
    embeddings = provider.embed_documents(texts)

    for chunk, embedding in zip(pending_chunks, embeddings):
        chunk.embedding = embedding

    await db.commit()
    return len(pending_chunks)