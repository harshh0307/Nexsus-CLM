import asyncio
import httpx
import os
import uuid

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "test_contract.pdf")

PASS = 0
FAIL = 0


def check(label, resp_status, expected_status, resp_body=""):
    global PASS, FAIL
    if resp_status == expected_status:
        PASS += 1
        print(f"  [PASS] {label} -> {resp_status}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label} -> got {resp_status}, expected {expected_status}")
        if resp_body:
            print(f"         Body: {str(resp_body)[:120]}")


async def main():
    global PASS, FAIL

    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=120.0) as client:
        print("=" * 60)
        print("NEGATIVE TEST CASES")
        print("=" * 60)

        # ─── AUTH TESTS ───────────────────────────────────────
        print("\n-- 1. AUTH TESTS --")

        # No token
        resp = await client.get("/api/contracts")
        check("GET /api/contracts with no token", resp.status_code, 401)

        # Invalid token
        resp = await client.get("/api/contracts", headers={"Authorization": "Bearer invalid_token_xyz"})
        check("GET /api/contracts with invalid token", resp.status_code, 401)

        # Expired/malformed token
        resp = await client.get("/api/contracts", headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.invalid"})
        check("GET /api/contracts with malformed JWT", resp.status_code, 401)

        # Login with wrong password
        resp = await client.post("/auth/login", json={"email": "test@example.com", "password": "wrongpassword"})
        check("Login with wrong password", resp.status_code, 401)

        # Login with non-existent email
        resp = await client.post("/auth/login", json={"email": "nonexistent@example.com", "password": "pass"})
        check("Login with non-existent email", resp.status_code, 401)

        # Register with short password
        resp = await client.post("/auth/register", json={"email": "new@test.com", "password": "ab", "name": "Test"})
        check("Register with short password", resp.status_code, 400)

        # Register with invalid email format
        resp = await client.post("/auth/register", json={"email": "not-an-email", "password": "pass123", "name": "Test"})
        check("Register with invalid email", resp.status_code, 422)

        # Register valid user first
        test_email = f"negative_{uuid.uuid4().hex[:8]}@test.com"
        resp = await client.post("/auth/register", json={"email": test_email, "password": "newpass456", "name": "Test User"})
        assert resp.status_code == 201, f"Setup registration failed: {resp.status_code} {resp.text}"
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Register with duplicate email (now should get 409)
        resp = await client.post("/auth/register", json={"email": test_email, "password": "pass123", "name": "Test"})
        check("Register with duplicate email", resp.status_code, 409)

        # Forgot password with invalid email format
        resp = await client.post("/auth/forgot-password", json={"email": "bad-email"})
        check("Forgot password with invalid email", resp.status_code, 422)

        # Reset password with invalid token
        resp = await client.post("/auth/reset-password", json={"token": "fake-token", "new_password": "newpass123"})
        check("Reset password with invalid token", resp.status_code, 400)

        # Get /auth/me without token
        resp = await client.get("/auth/me")
        check("GET /auth/me without token", resp.status_code, 401)

        # ─── CONTRACT UPLOAD TESTS ────────────────────────────
        print("\n-- 2. CONTRACT UPLOAD TESTS --")

        # Upload non-PDF file
        resp = await client.post(
            "/api/contracts/upload?party=company",
            headers=headers,
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )
        check("Upload non-PDF file", resp.status_code, 400)

        # Upload with invalid party
        with open(PDF_PATH, "rb") as f:
            resp = await client.post(
                "/api/contracts/upload?party=invalid",
                headers=headers,
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        check("Upload with invalid party value", resp.status_code, 400)

        # Upload without party param (should fail - party is required)
        with open(PDF_PATH, "rb") as f:
            resp = await client.post(
                "/api/contracts/upload",
                headers=headers,
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        check("Upload without party param", resp.status_code, 422)

        # Upload empty file
        resp = await client.post(
            "/api/contracts/upload?party=company",
            headers=headers,
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        # Empty PDF might still create a contract (pypdf handles it gracefully)
        check("Upload empty PDF", resp.status_code, 200)

        # ─── CONTRACT ACCESS TESTS ────────────────────────────
        print("\n-- 3. CONTRACT ACCESS TESTS --")

        # Get non-existent contract
        resp = await client.get(
            "/api/contracts/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        check("Get non-existent contract", resp.status_code, 404)

        # Analyze non-existent contract
        resp = await client.post(
            "/api/contracts/00000000-0000-0000-0000-000000000000/analyze",
            headers=headers,
            json={"extraction_queries": []},
        )
        check("Analyze non-existent contract", resp.status_code, 404)

        # Compare with non-existent company contract
        resp = await client.post(
            "/api/contracts/compare",
            headers=headers,
            json={
                "company_contract_id": "00000000-0000-0000-0000-000000000000",
                "client_contract_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        check("Compare with non-existent company contract", resp.status_code, 404)

        # Compare with non-existent client contract (need a real company ID first)
        resp = await client.post(
            "/api/contracts/upload?party=company",
            headers=headers,
            files={"file": ("temp.pdf", open(PDF_PATH, "rb"), "application/pdf")},
        )
        real_id = resp.json()["id"]

        resp = await client.post(
            "/api/contracts/compare",
            headers=headers,
            json={
                "company_contract_id": real_id,
                "client_contract_id": "00000000-0000-0000-0000-000000000001",
            },
        )
        check("Compare with non-existent client contract", resp.status_code, 404)

        # Compare with invalid UUID format
        resp = await client.post(
            "/api/contracts/compare",
            headers=headers,
            json={
                "company_contract_id": "not-a-uuid",
                "client_contract_id": "also-not-a-uuid",
            },
        )
        check("Compare with invalid UUID format", resp.status_code, 400)

        # ─── GUIDELINE TESTS ──────────────────────────────────
        print("\n-- 4. GUIDELINE TESTS --")

        # Upload empty guidelines
        resp = await client.post(
            "/api/guidelines/company",
            headers=headers,
            json={"guidelines": []},
        )
        check("Upload empty guidelines list", resp.status_code, 400)

        # Upload guideline with missing fields
        resp = await client.post(
            "/api/guidelines/company",
            headers=headers,
            json={"guidelines": [{"type": "test"}]},
        )
        check("Upload guideline with missing text", resp.status_code, 400)

        # Delete non-existent guideline
        resp = await client.delete(
            "/api/guidelines/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        check("Delete non-existent guideline", resp.status_code, 404)

        # Get related guidelines for non-existent guideline
        resp = await client.get(
            "/api/guidelines/related/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        check("Get related for non-existent guideline", resp.status_code, 404)

        # Get related guidelines with out-of-range sim values
        resp = await client.get(
            "/api/guidelines/related/00000000-0000-0000-0000-000000000000?min_sim=0.9&max_sim=0.1",
            headers=headers,
        )
        check("Get related with min > max sim", resp.status_code, 400)

        # ─── CROSS-USER ISOLATION TESTS ───────────────────────
        print("\n-- 5. CROSS-USER ISOLATION TESTS --")

        # Register a second user
        resp = await client.post(
            "/auth/register",
            json={"email": "other@example.com", "password": "pass123", "name": "Other"},
        )
        if resp.status_code == 201:
            other_token = resp.json()["access_token"]
            other_headers = {"Authorization": f"Bearer {other_token}"}

            # Other user tries to access first user's contracts
            resp = await client.get("/api/contracts", headers=other_headers)
            check("Other user lists contracts (should be empty)", resp.status_code, 200)
            # They should NOT see the first user's contracts
            if len(resp.json()) == 0:
                PASS += 1
                print(f"  [PASS] Other user sees 0 contracts (isolation works)")
            else:
                FAIL += 1
                print(f"  [FAIL] Other user sees {len(resp.json())} contracts (isolation broken)")

            # Other user tries to analyze first user's contract
            resp = await client.post(
                f"/api/contracts/{real_id}/analyze",
                headers=other_headers,
                json={"extraction_queries": []},
            )
            check("Other user analyzes first user's contract", resp.status_code, 404)

            # Other user tries to delete first user's guideline
            # First get a guideline ID from user 1
            resp1 = await client.get("/api/guidelines", headers=headers)
            if resp1.json():
                guid_id = resp1.json()[0]["id"]
                resp = await client.delete(f"/api/guidelines/{guid_id}", headers=other_headers)
                check("Other user deletes first user's guideline", resp.status_code, 404)
        else:
            print(f"  [SKIP] Could not register second user: {resp.status_code}")

        # ─── EDGE CASE TESTS ──────────────────────────────────
        print("\n-- 6. EDGE CASE TESTS --")

        # Analyze contract with very long extraction queries
        long_queries = [f"field_{i}" * 10 for i in range(50)]
        # First upload a fresh contract
        with open(PDF_PATH, "rb") as f:
            resp = await client.post(
                "/api/contracts/upload?party=company",
                headers=headers,
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        test_id = resp.json()["id"]

        resp = await client.post(
            f"/api/contracts/{test_id}/analyze",
            headers=headers,
            json={"extraction_queries": long_queries},
        )
        # Should still work or fail gracefully
        check("Analyze with 50 extraction queries", resp.status_code, 200)

        # Upload same PDF twice with different parties
        with open(PDF_PATH, "rb") as f:
            resp1 = await client.post(
                "/api/contracts/upload?party=company",
                headers=headers,
                files={"file": ("same.pdf", f, "application/pdf")},
            )
        with open(PDF_PATH, "rb") as f:
            resp2 = await client.post(
                "/api/contracts/upload?party=client",
                headers=headers,
                files={"file": ("same.pdf", f, "application/pdf")},
            )
        check("Upload same PDF as company", resp1.status_code, 200)
        check("Upload same PDF as client", resp2.status_code, 200)

        # Compare contract with itself
        if resp1.status_code == 200 and resp2.status_code == 200:
            cid1 = resp1.json()["id"]
            cid2 = resp2.json()["id"]
            resp = await client.post(
                "/api/contracts/compare",
                headers=headers,
                json={
                    "company_contract_id": cid1,
                    "client_contract_id": cid1,  # same contract
                },
            )
            check("Compare contract with itself", resp.status_code, 400)

        # List contracts with party filter (check party field is returned)
        resp = await client.get("/api/contracts", headers=headers)
        contracts = resp.json()
        has_party = all("party" in c for c in contracts)
        if has_party:
            PASS += 1
            print(f"  [PASS] All contracts have 'party' field")
        else:
            FAIL += 1
            print(f"  [FAIL] Some contracts missing 'party' field")

        # Check parties are mixed
        parties = {c.get("party") for c in contracts}
        if "company" in parties and "client" in parties:
            PASS += 1
            print(f"  [PASS] Both 'company' and 'client' parties present")
        else:
            FAIL += 1
            print(f"  [FAIL] Only parties: {parties}")

        # ─── SUMMARY ──────────────────────────────────────────
        print("\n" + "=" * 60)
        print(f"RESULTS: {PASS} passed, {FAIL} failed")
        print("=" * 60)

        if FAIL > 0:
            print("\nFailed tests need attention!")
        else:
            print("\nAll negative tests passed!")


asyncio.run(main())
