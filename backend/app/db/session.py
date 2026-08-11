import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
USE_POSTGRES = getattr(settings, "USE_POSTGRES", False)

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

_tables_created = False


async def init_db() -> None:
    """Create all tables and seed initial data. Safe to call multiple times."""
    global _tables_created
    if _tables_created:
        return
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _tables_created = True
        logger.info("FRAGMENT: DB tables initialized.")
    except Exception as e:
        logger.warning(f"FRAGMENT: Primary DB init failed ({e}), trying fallback SQLite...")
        try:
            fallback = create_async_engine(settings.SQLITE_FALLBACK_URL, echo=False, future=True)
            async with fallback.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            _tables_created = True
        except Exception as e2:
            logger.error(f"FRAGMENT: Fallback DB init also failed: {e2}")
            return

    try:
        from app.db.seed import seed_initial_data
        async with AsyncSessionLocal() as session:
            await seed_initial_data(session)
    except Exception as seed_err:
        logger.warning(f"FRAGMENT: Seed notice: {seed_err}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # Ensure tables exist before serving any request
    if not _tables_created:
        await init_db()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
