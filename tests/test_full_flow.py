import uuid

import httpx
import pytest

PDF_PATH = "test_contract.pdf"
pytestmark = pytest.mark.asyncio


class TestAuth:
    async def test_register_login(self, test_user):
        assert "token" in test_user
        assert "user_id" in test_user
        assert test_user["email"].startswith("pytest_")

    async def test_register_duplicate(self, client, test_user):
        r = await client.post("/auth/register", json={
            "email": test_user["email"], "password": "pass123", "name": "Dup",
        })
        assert r.status_code == 409

    async def test_login_wrong_password(self, client):
        r = await client.post("/auth/login", json={
            "email": "nonexistent@test.com", "password": "wrong",
        })
        assert r.status_code == 401

    async def test_no_token(self, client):
        r = await client.get("/api/contracts")
        assert r.status_code == 401

    async def test_invalid_token(self, client):
        r = await client.get("/api/contracts", headers={"Authorization": "Bearer invalid"})
        assert r.status_code == 401

    async def test_me_endpoint(self, client, test_user):
        r = await client.get("/auth/me", headers={"Authorization": f"Bearer {test_user['token']}"})
        assert r.status_code == 200
        assert r.json()["email"] == test_user["email"]

    async def test_short_password(self, client):
        r = await client.post("/auth/register", json={
            "email": "short@test.com", "password": "ab", "name": "Short",
        })
        assert r.status_code == 400


class TestSeedGuidelines:
    async def test_user_gets_seed_guidelines_on_register(self, test_user, headers, client):
        r = await client.get("/api/guidelines", headers=headers)
        assert r.status_code == 200
        guidelines = r.json()
        assert len(guidelines) == 18, f"Expected 18 seed guidelines, got {len(guidelines)}"
        scopes = {g["scope"] for g in guidelines}
        assert "company" in scopes
        assert "user" in scopes

    async def test_seed_guidelines_have_required_fields(self, test_user, headers, client):
        r = await client.get("/api/guidelines", headers=headers)
        guidelines = r.json()
        for g in guidelines:
            assert "id" in g
            assert "type" in g
            assert "text" in g
            assert "risk_level" in g
            assert "scope" in g


class TestContracts:
    async def test_upload_pdf(self, client, headers):
        with open(PDF_PATH, "rb") as f:
            r = await client.post(
                "/api/contracts/upload?party=company",
                headers=headers,
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["party"] == "company"
        assert data["status"] == "uploaded"

    async def test_upload_docx(self, client, headers):
        import io
        from docx import Document
        doc = Document()
        doc.add_paragraph("Test contract content for DOCX upload.")
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        r = await client.post(
            "/api/contracts/upload?party=client",
            headers=headers,
            files={"file": ("test.docx", buf, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["party"] == "client"
        assert data["status"] == "uploaded"

    async def test_upload_invalid_extension(self, client, headers):
        r = await client.post(
            "/api/contracts/upload?party=company",
            headers=headers,
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )
        assert r.status_code == 400

    async def test_upload_invalid_party(self, client, headers):
        with open(PDF_PATH, "rb") as f:
            r = await client.post(
                "/api/contracts/upload?party=invalid",
                headers=headers,
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        assert r.status_code == 400

    async def test_list_contracts(self, client, headers):
        r = await client.get("/api/contracts", headers=headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    async def test_list_contracts_isolation(self, client):
        r = await client.get("/api/contracts", headers={"Authorization": "Bearer invalid"})
        assert r.status_code == 401

    async def test_get_nonexistent_contract(self, client, headers):
        r = await client.get(
            "/api/contracts/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert r.status_code == 404

    async def test_contract_has_raw_text(self, client, headers):
        with open(PDF_PATH, "rb") as f:
            r = await client.post(
                "/api/contracts/upload?party=company",
                headers=headers,
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        cid = r.json()["id"]
        r = await client.get(f"/api/contracts/{cid}", headers=headers)
        data = r.json()
        assert data["raw_text_preview"] != "", "raw_text should not be empty"

    async def test_contract_party_field_returned(self, client, headers):
        with open(PDF_PATH, "rb") as f:
            await client.post(
                "/api/contracts/upload?party=company",
                headers=headers,
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        r = await client.get("/api/contracts", headers=headers)
        contracts = r.json()
        assert all("party" in c for c in contracts)


class TestAnalyze:
    async def test_analyze_contract(self, client, headers):
        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=600.0) as long_client:
            with open(PDF_PATH, "rb") as f:
                r = await long_client.post(
                    "/api/contracts/upload?party=company",
                    headers=headers,
                    files={"file": ("test.pdf", f, "application/pdf")},
                )
            cid = r.json()["id"]
            r = await long_client.post(
                f"/api/contracts/{cid}/analyze",
                headers=headers,
                json={"extraction_queries": []},
            )
        assert r.status_code == 200, f"Analyze failed: {r.status_code} {r.text[:200]}"
        data = r.json()
        assert "overall_risk_score" in data
        assert "clauses" in data
        assert "missing_clauses" in data
        assert "mismatches" in data
        assert "extracted_metadata" in data
        assert "party_conflicts" in data

    async def test_analyze_nonexistent(self, client, headers):
        r = await client.post(
            "/api/contracts/00000000-0000-0000-0000-000000000000/analyze",
            headers=headers,
            json={"extraction_queries": []},
        )
        assert r.status_code == 404


class TestCompare:
    async def test_compare_contracts(self, client, headers):
        with open(PDF_PATH, "rb") as f:
            r1 = await client.post(
                "/api/contracts/upload?party=company",
                headers=headers,
                files={"file": ("company.pdf", f, "application/pdf")},
            )
        with open(PDF_PATH, "rb") as f:
            r2 = await client.post(
                "/api/contracts/upload?party=client",
                headers=headers,
                files={"file": ("client.pdf", f, "application/pdf")},
            )
        cid1 = r1.json()["id"]
        cid2 = r2.json()["id"]
        r = await client.post(
            "/api/contracts/compare",
            headers=headers,
            json={"company_contract_id": cid1, "client_contract_id": cid2},
        )
        assert r.status_code == 200, f"Compare failed: {r.status_code} {r.text[:200]}"
        data = r.json()
        assert "company_analysis" in data
        assert "client_analysis" in data
        assert "cross_gaps" in data
        assert "term_conflicts" in data
        assert "overall_risk_score" in data

    async def test_compare_same_contract(self, client, headers):
        with open(PDF_PATH, "rb") as f:
            r = await client.post(
                "/api/contracts/upload?party=company",
                headers=headers,
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        cid = r.json()["id"]
        r = await client.post(
            "/api/contracts/compare",
            headers=headers,
            json={"company_contract_id": cid, "client_contract_id": cid},
        )
        assert r.status_code == 400

    async def test_compare_invalid_uuid(self, client, headers):
        r = await client.post(
            "/api/contracts/compare",
            headers=headers,
            json={"company_contract_id": "bad-uuid", "client_contract_id": "bad-uuid"},
        )
        assert r.status_code == 400


class TestGuidelines:
    async def test_upload_company_guidelines(self, client, headers):
        r = await client.post(
            "/api/guidelines/company",
            headers=headers,
            json={
                "guidelines": [
                    {"type": "test", "text": "Test guideline", "risk_level": "high"},
                ]
            },
        )
        assert r.status_code == 200
        assert r.json()["count"] == 1

    async def test_upload_user_guidelines(self, client, headers):
        r = await client.post(
            "/api/guidelines/user",
            headers=headers,
            json={
                "guidelines": [
                    {"type": "test", "text": "Client test guideline", "risk_level": "medium"},
                ]
            },
        )
        assert r.status_code == 200

    async def test_list_guidelines_includes_uploaded(self, client, headers):
        await client.post(
            "/api/guidelines/company",
            headers=headers,
            json={"guidelines": [{"type": "list_test", "text": "For listing", "risk_level": "low"}]},
        )
        r = await client.get("/api/guidelines", headers=headers)
        guidelines = r.json()
        types = [g["type"] for g in guidelines]
        assert "list_test" in types

    async def test_empty_guidelines_rejected(self, client, headers):
        r = await client.post(
            "/api/guidelines/company",
            headers=headers,
            json={"guidelines": []},
        )
        assert r.status_code == 400

    async def test_delete_guideline(self, client, headers):
        r = await client.post(
            "/api/guidelines/company",
            headers=headers,
            json={"guidelines": [{"type": "del_test", "text": "To delete", "risk_level": "low"}]},
        )
        guidelines = (await client.get("/api/guidelines", headers=headers)).json()
        to_delete = next(g for g in guidelines if g["type"] == "del_test")
        r = await client.delete(f"/api/guidelines/{to_delete['id']}", headers=headers)
        assert r.status_code == 200

    async def test_delete_nonexistent(self, client, headers):
        r = await client.delete(
            "/api/guidelines/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert r.status_code == 404


class TestCrossUserIsolation:
    async def test_cannot_access_other_users_contracts(self, client):
        suffix1 = uuid.uuid4().hex[:6]
        suffix2 = uuid.uuid4().hex[:6]
        r1 = await client.post("/auth/register", json={
            "email": f"user1_{suffix1}@test.com", "password": "pass123", "name": "User1",
        })
        token1 = r1.json()["access_token"]
        r2 = await client.post("/auth/register", json={
            "email": f"user2_{suffix2}@test.com", "password": "pass123", "name": "User2",
        })
        token2 = r2.json()["access_token"]

        with open(PDF_PATH, "rb") as f:
            r = await client.post(
                "/api/contracts/upload?party=company",
                headers={"Authorization": f"Bearer {token1}"},
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        cid = r.json()["id"]

        r = await client.get("/api/contracts", headers={"Authorization": f"Bearer {token2}"})
        assert len(r.json()) == 0, "User2 should see 0 contracts"

        r = await client.post(
            f"/api/contracts/{cid}/analyze",
            headers={"Authorization": f"Bearer {token2}"},
            json={"extraction_queries": []},
        )
        assert r.status_code == 404


class TestHealth:
    async def test_health_endpoint(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
