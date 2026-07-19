import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from pypdf import PdfReader
from sqlmodel import select

from app.db.engine import get_session
from app.db.models import Contract, User
from app.security.auth import get_current_user

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

UPLOAD_DIR = "/app/uploads"


@router.post("/upload")
async def upload_contract(
    file: UploadFile,
    party: str = Query(..., description="'company' or 'client'"),
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    if party not in ("company", "client"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="party must be 'company' or 'client'")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    safe_name = f"{file_id}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, safe_name)

    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    raw_text = ""
    try:
        reader = PdfReader(path)
        for page in reader.pages:
            raw_text += page.extract_text() or ""
    except Exception:
        pass

    contract = Contract(
        tenant_id=str(user.id),
        file_name=file.filename,
        storage_path=path,
        status="uploaded",
        party=party,
        raw_text=raw_text,
    )
    session.add(contract)
    await session.commit()
    await session.refresh(contract)

    return {
        "id": str(contract.id),
        "file_name": contract.file_name,
        "status": contract.status,
        "party": contract.party,
        "created_at": contract.created_at.isoformat(),
    }


@router.get("")
async def list_contracts(
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    stmt = (
        select(Contract)
        .where(Contract.tenant_id == str(user.id))
        .order_by(Contract.created_at.desc())
    )
    results = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": str(c.id),
            "file_name": c.file_name,
            "status": c.status,
            "party": c.party,
            "created_at": c.created_at.isoformat(),
        }
        for c in results
    ]


@router.get("/{contract_id}")
async def get_contract(
    contract_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    stmt = select(Contract).where(
        Contract.id == contract_id,
        Contract.tenant_id == str(user.id),
    )
    contract = (await session.execute(stmt)).scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return {
        "id": str(contract.id),
        "file_name": contract.file_name,
        "status": contract.status,
        "party": contract.party,
        "extracted_metadata": contract.extracted_metadata,
        "raw_text_preview": contract.raw_text[:500] if contract.raw_text else "",
        "created_at": contract.created_at.isoformat(),
        "updated_at": contract.updated_at.isoformat(),
    }
