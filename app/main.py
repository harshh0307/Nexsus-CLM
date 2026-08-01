from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from app.api.analysis import router as analysis_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.contracts import router as contracts_router
from app.api.guidelines import router as guidelines_router
from app.db.engine import async_session, init_db
from app.db.seed import seed_guidelines
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session() as session:
        await seed_guidelines(session)
    yield


app = FastAPI(title="NexusCLM", version="0.3.0", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(contracts_router)
app.include_router(guidelines_router)
app.include_router(analysis_router)
app.include_router(analytics_router)

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/ui", StaticFiles(directory=frontend_dir, html=True), name="ui")


@app.get("/health")
async def health():
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unreachable"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "nexus-clm",
        "database": db_status,
    }
