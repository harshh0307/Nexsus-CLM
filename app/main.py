from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.contracts import router as contracts_router
from app.api.extraction import router as extraction_router
from app.db.engine import async_session, init_db
from app.db.seed import seed_guidelines


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session() as session:
        await seed_guidelines(session)
    yield


app = FastAPI(title="NexusCLM", version="0.1.0", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(contracts_router)
app.include_router(extraction_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "nexus-clm"}
