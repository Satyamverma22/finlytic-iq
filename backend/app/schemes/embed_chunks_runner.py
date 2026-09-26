# app/schemes/embed_chunks_runner.py

import asyncio

from app.core.database import AsyncSessionLocal
from app.schemes.embedding_pipeline import embed_pending_chunks


async def main():
    async with AsyncSessionLocal() as db:
        count = await embed_pending_chunks(db)
        print(f"Embedded {count} chunk(s).")


if __name__ == "__main__":
    asyncio.run(main())