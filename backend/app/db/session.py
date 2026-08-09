import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

# Use SQLite by default for lightweight local development unless POSTGRES_DB is explicitly enabled
# Dynamic DB path: use /tmp in serverless Vercel environments
IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

if USE_POSTGRES:
    db_url = settings.DATABASE_URL
elif IS_VERCEL:
    db_url = "sqlite+aiosqlite:////tmp/fragment.db"
else:
    db_url = settings.SQLITE_FALLBACK_URL

engine = create_async_engine(db_url, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    """Initialize database tables and seed initial 2 real-world quantitative option models."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Primary database connection failed ({e}), falling back to SQLite async engine.")
        fallback_engine = create_async_engine(settings.SQLITE_FALLBACK_URL, echo=False, future=True)
        async with fallback_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Seed initial 2 quantitative option models with full validation reports
    from app.db.seed import seed_initial_data
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)
