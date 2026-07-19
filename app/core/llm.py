import json
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


async def llm_complete(system_prompt: str, user_prompt: str, response_model: dict[str, Any] | None = None) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    body: dict[str, Any] = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": 0.1,
    }
    if response_model:
        body["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers=_get_headers(),
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def extract_json(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    raw = await llm_complete(system_prompt=system_prompt, user_prompt=user_prompt, response_model={"type": "json_object"})
    return json.loads(raw)
