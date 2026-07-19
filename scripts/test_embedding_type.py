import asyncio
from app.db.engine import async_session
from sqlmodel import select
from app.db.models import UserGuideline

async def test():
    async with async_session() as session:
        stmt = select(UserGuideline).where(UserGuideline.embedding.is_not(None)).limit(1)
        result = await session.execute(stmt)
        guideline = result.scalar_one_or_none()
        if guideline:
            emb = guideline.embedding
            print(f"Type: {type(emb)}")
            print(f"Repr: {repr(emb)[:200]}")
            try:
                converted = list(emb)
                print(f"list() works: {len(converted)} items, type={type(converted[0])}")
            except Exception as e:
                print(f"list() failed: {e}")
            try:
                import numpy as np
                arr = np.array(emb, dtype=float)
                print(f"np.array works: {arr.shape}, dtype={arr.dtype}")
            except Exception as e:
                print(f"np.array failed: {e}")

asyncio.run(test())
