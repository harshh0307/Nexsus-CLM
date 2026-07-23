import httpx


class NexusCLMClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = ""

    def set_token(self, token: str):
        self.token = token

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    async def register(self, email: str, password: str, name: str) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{self.base_url}/auth/register", json={"email": email, "password": password, "name": name})
            if r.status_code == 201:
                d = r.json()
                self.set_token(d["access_token"])
                return {"success": True, "data": d}
            detail = r.json().get("detail", r.text) if r.text else r.status_code
            return {"success": False, "error": str(detail)}

    async def login(self, email: str, password: str) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{self.base_url}/auth/login", json={"email": email, "password": password})
            if r.status_code == 200:
                d = r.json()
                self.set_token(d["access_token"])
                return {"success": True, "data": d}
            detail = r.json().get("detail", r.text) if r.text else r.status_code
            return {"success": False, "error": str(detail)}

    async def list_contracts(self) -> list:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{self.base_url}/api/contracts", headers=self._headers())
            if r.status_code == 200:
                return r.json()
            return []

    async def get_contract(self, contract_id: str) -> dict | None:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{self.base_url}/api/contracts/{contract_id}", headers=self._headers())
            if r.status_code == 200:
                return r.json()
            return None

    async def upload_contract(self, file_path: str, party: str) -> dict:
        async with httpx.AsyncClient() as c:
            with open(file_path, "rb") as f:
                r = await c.post(
                    f"{self.base_url}/api/contracts/upload?party={party}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    files={"file": f},
                )
                if r.status_code == 200:
                    return {"success": True, "data": r.json()}
                detail = r.json().get("detail", r.text) if r.text else r.status_code
                return {"success": False, "error": str(detail)}

    async def analyze_contract(self, contract_id: str) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{self.base_url}/api/contracts/{contract_id}/analyze",
                headers=self._headers(),
                json={"extraction_queries": []},
            )
            if r.status_code == 200:
                return {"success": True, "data": r.json()}
            detail = r.json().get("detail", r.text) if r.text else r.status_code
            return {"success": False, "error": str(detail)}

    async def compare_contracts(self, company_id: str, client_id: str) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{self.base_url}/api/contracts/compare",
                headers=self._headers(),
                json={"company_contract_id": company_id, "client_contract_id": client_id},
            )
            if r.status_code == 200:
                return {"success": True, "data": r.json()}
            detail = r.json().get("detail", r.text) if r.text else r.status_code
            return {"success": False, "error": str(detail)}

    async def list_guidelines(self) -> list:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{self.base_url}/api/guidelines", headers=self._headers())
            if r.status_code == 200:
                return r.json()
            return []

    async def upload_company_guidelines(self, guidelines: list) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{self.base_url}/api/guidelines/company",
                headers=self._headers(),
                json={"guidelines": guidelines},
            )
            if r.status_code == 200:
                return {"success": True, "data": r.json()}
            detail = r.json().get("detail", r.text) if r.text else r.status_code
            return {"success": False, "error": str(detail)}

    async def upload_user_guidelines(self, guidelines: list) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{self.base_url}/api/guidelines/user",
                headers=self._headers(),
                json={"guidelines": guidelines},
            )
            if r.status_code == 200:
                return {"success": True, "data": r.json()}
            detail = r.json().get("detail", r.text) if r.text else r.status_code
            return {"success": False, "error": str(detail)}

    async def delete_guideline(self, guid: str) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.delete(f"{self.base_url}/api/guidelines/{guid}", headers=self._headers())
            if r.status_code == 200:
                return {"success": True}
            detail = r.json().get("detail", r.text) if r.text else r.status_code
            return {"success": False, "error": str(detail)}

    async def get_dashboard(self) -> dict:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{self.base_url}/api/analytics/dashboard", headers=self._headers())
            if r.status_code == 200:
                return r.json()
            return {}
