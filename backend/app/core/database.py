# app/core/database.py

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class every ORM model will inherit from."""
    pass


# asyncpg needs a slightly different URL scheme than the plain 'postgresql://'
# used by psycopg2/Alembic, so we convert it here rather than maintaining
# two separate URLs in .env.
ASYNC_DATABASE_URL = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://", 1
)

engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency — yields a DB session per request, closes it after."""
    async with AsyncSessionLocal() as session:
        yield session