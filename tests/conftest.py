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


@pytest_asyncio.fixture
async def uploaded_contract(client: httpx.AsyncClient, headers: dict, party: str = "company"):
    with open(PDF_PATH, "rb") as f:
        r = await client.post(
            f"/api/contracts/upload?party={party}",
            headers=headers,
            files={"file": ("test.pdf", f, "application/pdf")},
        )
    assert r.status_code == 200, f"Upload failed: {r.status_code} {r.text}"
    return r.json()["id"]
