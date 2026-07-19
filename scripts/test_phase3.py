import asyncio
import httpx
import os

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "test_contract.pdf")


async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=300.0) as client:
        print("=" * 60)
        print("PHASE 4 FULL FLOW TEST")
        print("=" * 60)

        # 1. Login (register first if needed)
        resp = await client.post("/auth/login", json={"email": "test@example.com", "password": "newpass456"})
        if resp.status_code != 200:
            await client.post("/auth/register", json={"email": "test@example.com", "password": "newpass456", "name": "Test User"})
            resp = await client.post("/auth/login", json={"email": "test@example.com", "password": "newpass456"})
        data = resp.json()
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"\n1. Login OK: {data['email']}")

        # 2. Upload company guidelines
        print("\n2. Uploading company guidelines...")
        company_guidelines = {
            "guidelines": [
                {"type": "indemnification", "text": "Indemnification must be mutual for both parties", "risk_level": "high"},
                {"type": "liability", "text": "Liability cap must be at least $2M per occurrence", "risk_level": "high"},
                {"type": "termination", "text": "Termination for convenience requires 60 days written notice", "risk_level": "medium"},
                {"type": "confidentiality", "text": "Confidentiality obligations must survive for 5 years post-termination", "risk_level": "high"},
                {"type": "data_protection", "text": "All data must be encrypted at rest and in transit using AES-256 and TLS 1.2", "risk_level": "high"},
                {"type": "insurance", "text": "Vendor must maintain $5M umbrella liability insurance", "risk_level": "high"},
                {"type": "warranty", "text": "Services warranty must include workmanlike performance standard for 12 months", "risk_level": "medium"},
                {"type": "payment", "text": "Payment terms must be net 30 or better", "risk_level": "low"},
            ]
        }
        resp = await client.post("/api/guidelines/company", headers=headers, json=company_guidelines)
        print(f"   Company guidelines: {resp.json()}")

        # 3. Upload client guidelines
        print("\n3. Uploading client guidelines...")
        client_guidelines = {
            "guidelines": [
                {"type": "indemnification", "text": "Indemnification cap must not exceed 25% of total contract value", "risk_level": "high"},
                {"type": "liability", "text": "Liability cap must not exceed the total contract value", "risk_level": "high"},
                {"type": "termination", "text": "Termination for convenience requires 30 days written notice", "risk_level": "medium"},
                {"type": "confidentiality", "text": "Confidentiality obligations must survive for 3 years post-termination", "risk_level": "medium"},
                {"type": "governing_law", "text": "Governing law should be Delaware or New York", "risk_level": "medium"},
                {"type": "warranty", "text": "Products must be free from defects for 12 months", "risk_level": "medium"},
            ]
        }
        resp = await client.post("/api/guidelines/user", headers=headers, json=client_guidelines)
        print(f"   Client guidelines: {resp.json()}")

        # 4. Upload company contract
        print("\n4. Uploading company contract (party=company)...")
        with open(PDF_PATH, "rb") as f:
            files = {"file": ("company_contract.pdf", f, "application/pdf")}
            resp = await client.post("/api/contracts/upload?party=company", headers=headers, files=files)
            company_contract = resp.json()
            company_id = company_contract["id"]
            print(f"   Company contract: {company_id} (party={company_contract.get('party', 'N/A')})")

        # 5. Upload client contract (same PDF for testing, in reality it would be different)
        print("\n5. Uploading client contract (party=client)...")
        with open(PDF_PATH, "rb") as f:
            files = {"file": ("client_contract.pdf", f, "application/pdf")}
            resp = await client.post("/api/contracts/upload?party=client", headers=headers, files=files)
            client_contract = resp.json()
            client_id = client_contract["id"]
            print(f"   Client contract: {client_id} (party={client_contract.get('party', 'N/A')})")

        # 6. List contracts
        print("\n6. Listing all contracts...")
        resp = await client.get("/api/contracts", headers=headers)
        contracts = resp.json()
        print(f"   Total contracts: {len(contracts)}")
        for c in contracts:
            print(f"   - [{c.get('party', 'N/A')}] {c['file_name']} ({c['status']})")

        # 7. Analyze company contract individually
        print("\n7. Analyzing company contract individually...")
        resp = await client.post(
            f"/api/contracts/{company_id}/analyze",
            headers=headers,
            json={"extraction_queries": ["indemnification cap amount", "termination notice period in days"]}
        )
        if resp.status_code == 200:
            company_result = resp.json()
            print(f"   Risk Score: {company_result['overall_risk_score']}")
            print(f"   Clauses: {len(company_result.get('clauses', []))}")
            print(f"   Missing: {len(company_result.get('missing_clauses', []))}")
        else:
            print(f"   ERROR: {resp.status_code} - {resp.text[:200]}")
            company_result = None

        # 8. Compare both contracts
        print("\n8. Comparing company vs client contracts...")
        resp = await client.post(
            "/api/contracts/compare",
            headers=headers,
            json={
                "company_contract_id": company_id,
                "client_contract_id": client_id,
                "extraction_queries": ["indemnification cap amount", "termination notice period in days"],
            }
        )

        if resp.status_code == 200:
            comparison = resp.json()
            print("\n" + "=" * 60)
            print("COMPARISON COMPLETE")
            print("=" * 60)

            print(f"\nOverall Risk Score: {comparison['overall_risk_score']}")
            print(f"Risk Summary: {comparison['risk_summary']}")

            print(f"\n--- Company Analysis ---")
            ca = comparison.get("company_analysis", {})
            print(f"  Risk: {ca.get('overall_risk_score', 'N/A')}")
            print(f"  Clauses: {len(ca.get('clauses', []))}")
            print(f"  Missing: {len(ca.get('missing_clauses', []))}")

            print(f"\n--- Client Analysis ---")
            cl = comparison.get("client_analysis", {})
            print(f"  Risk: {cl.get('overall_risk_score', 'N/A')}")
            print(f"  Clauses: {len(cl.get('clauses', []))}")
            print(f"  Missing: {len(cl.get('missing_clauses', []))}")

            print(f"\n--- Cross Gaps: {len(comparison.get('cross_gaps', []))} ---")
            for g in comparison.get("cross_gaps", []):
                print(f"  [{g.get('severity', 'medium').upper()}] {g.get('clause_type', 'N/A')}")
                print(f"    Present in: {g.get('present_in', 'N/A')}")
                print(f"    Missing from: {g.get('missing_from', 'N/A')}")
                print(f"    -> {g.get('recommendation', 'N/A')}")

            print(f"\n--- Term Conflicts: {len(comparison.get('term_conflicts', []))} ---")
            for c in comparison.get("term_conflicts", []):
                print(f"  [{c.get('severity', 'medium').upper()}] {c.get('clause_type', 'N/A')}")
                print(f"    Company: {c.get('company_term', 'N/A')[:80]}...")
                print(f"    Client: {c.get('client_term', 'N/A')[:80]}...")
                print(f"    -> {c.get('resolution_suggestion', 'N/A')}")

        else:
            print(f"\nERROR: {resp.status_code}")
            print(resp.text[:500])

        # 9. Find related guidelines
        print("\n9. Finding related guidelines...")
        resp = await client.get("/api/guidelines", headers=headers)
        guidelines = resp.json()
        if guidelines:
            first_guideline_id = guidelines[0]["id"]
            resp = await client.get(f"/api/guidelines/related/{first_guideline_id}", headers=headers)
            if resp.status_code == 200:
                related_result = resp.json()
                print(f"   Source: [{related_result['source_guideline']['type']}] {related_result['source_guideline']['text'][:60]}...")
                print(f"   Related: {related_result['count']} guidelines found")
                for r in related_result.get("related_guidelines", []):
                    print(f"     - [{r['type']}] sim={r['similarity_score']:.3f} | {r['text'][:60]}...")
            else:
                print(f"   ERROR: {resp.status_code}")

asyncio.run(main())
