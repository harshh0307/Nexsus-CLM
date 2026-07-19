import asyncio
from app.db.engine import async_session
from sqlalchemy import text

async def test():
    async with async_session() as session:
        r = await session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        print("pgvector extension:", r.fetchall())
        
        r2 = await session.execute(text("SELECT id, guideline_type, guideline_scope FROM user_guidelines LIMIT 3"))
        print("Guidelines:", r2.fetchall())
        
        # Test raw SQL vector query with a 1536-dim zero vector
        zero_vec = "[" + ",".join(["0.0"] * 1536) + "]"
        r3 = await session.execute(
            text("SELECT id, guideline_type, guideline_scope, 1 - (embedding <=> :embedding::vector) as similarity FROM user_guidelines WHERE embedding IS NOT NULL LIMIT 3"),
            {"embedding": zero_vec}
        )
        rows = r3.fetchall()
        print("Vector query results:", len(rows))
        for row in rows:
            print(f"  {row[1]} ({row[2]}): {row[3]}")

asyncio.run(test())
