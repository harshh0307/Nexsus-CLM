import uuid
from datetime import datetime, timezone

_naive_utc = lambda: datetime.now(timezone.utc).replace(tzinfo=None)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.core.dynamic_schema import extract_fields, generate_schema
from app.db.engine import get_session
from app.db.models import AuditLog, Contract, User
from app.security.auth import get_current_user

router = APIRouter(prefix="/api/contracts", tags=["extraction"])


@router.post("/{contract_id}/extract")
async def extract_contract(
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

    if not contract.raw_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contract has no raw text to extract")

    try:
        schema = await generate_schema(contract.raw_text, [])
        extracted = await extract_fields(contract.raw_text, schema)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Extraction failed: {str(e)}")

    contract.extracted_metadata = extracted
    contract.status = "extracted"
    contract.updated_at = _naive_utc()

    audit = AuditLog(
        tenant_id=str(user.id),
        contract_id=contract.id,
        action="contract_extracted",
        performed_by=str(user.id),
        details={"schema_fields": list(schema.keys()) if isinstance(schema, dict) else []},
    )
    session.add(audit)
    await session.commit()
    await session.refresh(contract)

    return {
        "id": str(contract.id),
        "status": contract.status,
        "extracted_metadata": contract.extracted_metadata,
    }
