import uuid

import httpx
import pytest
import pytest_asyncio

BASE_URL = "http://localhost:8000"
PDF_PATH = "test_contract.pdf"


@pytest_asyncio.fixture
async def client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as c:
        yield c


@pytest_asyncio.fixture
async def test_user(client: httpx.AsyncClient):
    suffix = uuid.uuid4().hex[:8]
    email = f"pytest_{suffix}@test.com"
    r = await client.post("/auth/register", json={
        "email": email, "password": "testpass123", "name": "Pytest User",
    })
    assert r.status_code == 201, f"Register failed: {r.status_code} {r.text}"
    data = r.json()
    return {
        "email": email,
        "token": data["access_token"],
        "user_id": data["user_id"],
        "name": data["name"],
    }


@pytest_asyncio.fixture
async def headers(test_user):
    return {"Authorization": f"Bearer {test_user['token']}"}
