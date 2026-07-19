import asyncio
from typing import Any

import httpx

from app.config import settings


def _get_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    elif settings.openai_api_key:
        headers["Authorization"] = f"Bearer {settings.openai_api_key}"
    return headers


async def generate_embedding(text: str) -> list[float]:
    """Generate 1536-dim embedding for text using text-embedding-3-small."""
    max_retries = 5
    for attempt in range(max_retries):
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.embedding_url.rstrip('/')}/embeddings",
                headers=_get_headers(),
                json={
                    "model": settings.embedding_model,
                    "input": text[:8000],
                },
            )
            if resp.status_code == 429 and attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt * 5)
                continue
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts."""
    max_retries = 5
    for attempt in range(max_retries):
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.embedding_url.rstrip('/')}/embeddings",
                headers=_get_headers(),
                json={
                    "model": settings.embedding_model,
                    "input": [t[:8000] for t in texts],
                },
            )
            if resp.status_code == 429 and attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt * 5)
                continue
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
