import uuid
from datetime import datetime, timezone

_naive_utc = lambda: datetime.now(timezone.utc).replace(tzinfo=None)

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select

from app.core.embedding import generate_embeddings
from app.core.risk_analyzer import find_related_guidelines as _find_related
from app.db.engine import get_session
from app.db.models import User, UserGuideline
from app.schemas.analysis import GuidelineUploadRequest
from app.security.auth import get_current_user

router = APIRouter(prefix="/api/guidelines", tags=["guidelines"])


@router.post("/company")
async def upload_company_guidelines(
    body: GuidelineUploadRequest,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """Upload company guidelines (what the company requires)."""
    return await _upload_guidelines(body, user, session, "company")


@router.post("/user")
async def upload_user_guidelines(
    body: GuidelineUploadRequest,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """Upload user/client guidelines (what the user requires)."""
    return await _upload_guidelines(body, user, session, "user")


async def _upload_guidelines(
    body: GuidelineUploadRequest,
    user: User,
    session,
    scope: str,
):
    texts = [g.get("text", "") for g in body.guidelines]
    if not texts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No guidelines provided")

    # Filter out guidelines with empty text
    valid_guidelines = [g for g in body.guidelines if g.get("text", "").strip()]
    if not valid_guidelines:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All guidelines have empty text")

    texts = [g.get("text", "") for g in valid_guidelines]
    embeddings = await generate_embeddings(texts)

    created = []
    for guideline, embedding in zip(valid_guidelines, embeddings):
        record = UserGuideline(
            tenant_id=str(user.id),
            guideline_type=guideline.get("type", "other"),
            standard_text=guideline.get("text", ""),
            risk_level=guideline.get("risk_level", "medium"),
            guideline_scope=scope,
            embedding=embedding,
        )
        session.add(record)
        created.append(record)

    await session.commit()
    for record in created:
        await session.refresh(record)

    return {
        "message": f"Uploaded {len(created)} {scope} guidelines",
        "count": len(created),
    }


@router.get("")
async def list_guidelines(
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """List all guidelines for the current user."""
    stmt = (
        select(UserGuideline)
        .where(UserGuideline.tenant_id == str(user.id))
        .order_by(UserGuideline.created_at.desc())
    )
    results = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": str(g.id),
            "type": g.guideline_type,
            "text": g.standard_text,
            "risk_level": g.risk_level,
            "scope": g.guideline_scope,
            "created_at": g.created_at.isoformat(),
        }
        for g in results
    ]


@router.delete("/{guideline_id}")
async def delete_guideline(
    guideline_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """Delete a guideline."""
    stmt = select(UserGuideline).where(
        UserGuideline.id == guideline_id,
        UserGuideline.tenant_id == str(user.id),
    )
    guideline = (await session.execute(stmt)).scalar_one_or_none()
    if not guideline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guideline not found")
    await session.delete(guideline)
    await session.commit()
    return {"message": "Guideline deleted"}


@router.get("/related/{guideline_id}")
async def find_related_guidelines(
    guideline_id: uuid.UUID,
    min_sim: float = Query(0.3, ge=0.0, le=1.0),
    max_sim: float = Query(0.5, ge=0.0, le=1.0),
    top_k: int = Query(5, ge=1, le=20),
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """Find guidelines semantically similar to a given guideline."""
    if min_sim >= max_sim:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="min_sim must be less than max_sim")
    stmt = select(UserGuideline).where(
        UserGuideline.id == guideline_id,
        UserGuideline.tenant_id == str(user.id),
    )
    guideline = (await session.execute(stmt)).scalar_one_or_none()
    if not guideline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guideline not found")

    if not guideline.embedding:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Guideline has no embedding")

    # Convert embedding to a plain Python list of floats
    embedding_list = [float(x) for x in guideline.embedding]

    related = await _find_related(
        embedding_list,
        str(user.id),
        session,
        min_sim=min_sim,
        max_sim=max_sim,
        top_k=top_k,
    )

    return {
        "source_guideline": {
            "id": str(guideline.id),
            "type": guideline.guideline_type,
            "text": guideline.standard_text,
            "scope": guideline.guideline_scope,
        },
        "related_guidelines": [
            {
                "id": r["guideline_id"],
                "type": r["guideline_type"],
                "text": r["standard_text"],
                "scope": r["guideline_scope"],
                "similarity_score": r["similarity_score"],
            }
            for r in related
        ],
        "count": len(related),
    }
