from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.config import settings
from app.db.models import *

engine = create_async_engine(settings.database_url, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        # Add party column to contracts table if it doesn't exist
        await conn.execute(text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS party VARCHAR DEFAULT 'company'"
        ))


async def get_session():
    async with async_session() as session:
        yield session
