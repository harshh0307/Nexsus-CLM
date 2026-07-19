import asyncio
import httpx
import os

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "test_contract.pdf")

async def main():
    # 1. Login
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        resp = await client.post("/auth/login", json={"email": "test@example.com", "password": "newpass456"})
        data = resp.json()
        token = data["access_token"]
        print(f"Login OK: token={token[:30]}...")

        # 2. Upload PDF
        with open(PDF_PATH, "rb") as f:
            files = {"file": ("test_contract.pdf", f, "application/pdf")}
            resp = await client.post("/api/contracts/upload", headers={"Authorization": f"Bearer {token}"}, files=files)
            contract = resp.json()
            print(f"Upload OK: id={contract['id']}, status={contract['status']}")

        # 3. Get contract details
        resp = await client.get(f"/api/contracts/{contract['id']}", headers={"Authorization": f"Bearer {token}"})
        detail = resp.json()
        print(f"Detail OK: status={detail['status']}")

        # 4. List contracts
        resp = await client.get("/api/contracts", headers={"Authorization": f"Bearer {token}"})
        contracts = resp.json()
        items = contracts.get("value", contracts) if isinstance(contracts, dict) else contracts
        print(f"List OK: {len(items)} contracts")

        # 5. Extract (calls LLM)
        print("\n--- Starting extraction (calling LLM) ---")
        resp = await client.post(f"/api/contracts/{contract['id']}/extract", headers={"Authorization": f"Bearer {token}"}, timeout=120.0)
        if resp.status_code == 200:
            result = resp.json()
            print(f"Extraction OK: status={result['status']}")
            meta = result.get("extracted_metadata", {})
            print(f"Extracted fields: {list(meta.keys()) if meta else 'empty'}")
            if meta:
                for k, v in list(meta.items())[:5]:
                    print(f"  {k}: {str(v)[:80]}")
        else:
            print(f"Extraction FAILED: {resp.status_code}")
            print(resp.text[:1000])

asyncio.run(main())
