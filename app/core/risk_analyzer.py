import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import extract_json
from app.db.models import UserGuideline

_COMPLIANCE_PROMPT = """You are a legal compliance analyzer. Analyze whether a contract clause meets a specific guideline.

Contract clause:
{clause_text}

Guideline:
{guideline_text}

Determine the compliance status:
- "compliant": The clause fully meets the guideline requirement
- "non_compliant": The clause violates or does not meet the guideline
- "partial": The clause partially meets the guideline
- "not_applicable": The guideline does not apply to this clause

Return JSON:
{{
  "compliance_status": "compliant|non_compliant|partial|not_applicable",
  "analysis": "Brief explanation of why this status was assigned"
}}

Return ONLY valid JSON with no markdown or explanation."""


async def analyze_clause_compliance(
    clause_text: str,
    guideline_text: str,
) -> dict[str, Any]:
    """Use LLM to determine compliance status for a clause-guideline pair."""
    prompt = _COMPLIANCE_PROMPT.format(
        clause_text=clause_text[:4000],
        guideline_text=guideline_text[:2000]
    )
    result = await extract_json(
        "You are a legal compliance analysis system.",
        prompt
    )
    return {
        "compliance_status": result.get("compliance_status", "not_applicable"),
        "llm_analysis": result.get("analysis", "")
    }


async def find_matching_guidelines(
    clause_embedding: list[float],
    tenant_id: str,
    session: AsyncSession,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Find matching guidelines using pgvector cosine similarity."""
    import pgvector.sqlalchemy  # noqa: F401

    embedding_str = "[" + ",".join(str(x) for x in clause_embedding) + "]"
    cosine_dist = UserGuideline.embedding.cosine_distance(embedding_str)

    stmt = (
        select(
            UserGuideline.id,
            UserGuideline.guideline_type,
            UserGuideline.standard_text,
            UserGuideline.risk_level,
            UserGuideline.guideline_scope,
            (1 - cosine_dist).label("similarity"),
        )
        .where(
            UserGuideline.tenant_id == tenant_id,
            UserGuideline.embedding.is_not(None),
        )
        .order_by(cosine_dist)
        .limit(top_k)
    )

    result = await session.execute(stmt)
    rows = result.fetchall()
    return [
        {
            "guideline_id": str(row[0]),
            "guideline_type": row[1],
            "standard_text": row[2],
            "risk_level": row[3],
            "guideline_scope": row[4],
            "similarity_score": float(row[5]),
        }
        for row in rows
    ]


async def find_related_guidelines(
    clause_embedding: list[float],
    tenant_id: str,
    session: AsyncSession,
    min_sim: float = 0.3,
    max_sim: float = 0.5,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Find semantically related guidelines (not direct matches)."""
    import pgvector.sqlalchemy  # noqa: F401
    import numpy as np

    embedding_arr = np.array(clause_embedding, dtype=np.float32)
    cosine_dist = UserGuideline.embedding.cosine_distance(embedding_arr)

    # Get more candidates then filter in Python to avoid pgvector operator issues
    stmt = (
        select(
            UserGuideline.id,
            UserGuideline.guideline_type,
            UserGuideline.standard_text,
            UserGuideline.risk_level,
            UserGuideline.guideline_scope,
            (1 - cosine_dist).label("similarity"),
        )
        .where(
            UserGuideline.tenant_id == tenant_id,
            UserGuideline.embedding.is_not(None),
        )
        .order_by(cosine_dist)
        .limit(top_k * 3)
    )

    result = await session.execute(stmt)
    rows = result.fetchall()

    # Filter by similarity range in Python
    filtered = []
    for row in rows:
        sim = float(row[5])
        if min_sim <= sim <= max_sim:
            filtered.append({
                "guideline_id": str(row[0]),
                "guideline_type": row[1],
                "standard_text": row[2],
                "risk_level": row[3],
                "guideline_scope": row[4],
                "similarity_score": sim,
            })
            if len(filtered) >= top_k:
                break

    return filtered


async def analyze_clauses(
    clauses: list[dict[str, Any]],
    clause_embeddings: list[list[float]],
    tenant_id: str,
    session: AsyncSession,
) -> list[dict[str, Any]]:
    """Analyze all clauses against guidelines with two-tier matching."""
    results = []
    for clause, embedding in zip(clauses, clause_embeddings):
        # Tier 1: Direct matches (similarity > 0.5) — full compliance analysis
        matches = await find_matching_guidelines(embedding, tenant_id, session)

        company_matches = [m for m in matches if m["guideline_scope"] == "company"]
        user_matches = [m for m in matches if m["guideline_scope"] == "user"]

        analyzed_company = []
        for m in company_matches:
            if m["similarity_score"] > 0.5:
                compliance = await analyze_clause_compliance(
                    clause["text_content"], m["standard_text"]
                )
                analyzed_company.append({**m, **compliance, "discovery_type": "direct_match"})

        analyzed_user = []
        for m in user_matches:
            if m["similarity_score"] > 0.5:
                compliance = await analyze_clause_compliance(
                    clause["text_content"], m["standard_text"]
                )
                analyzed_user.append({**m, **compliance, "discovery_type": "direct_match"})

        # Tier 2: Semantic discoveries (similarity 0.3-0.5) — flagged as related
        related = await find_related_guidelines(embedding, tenant_id, session)

        for m in related:
            entry = {**m, "compliance_status": "not_applicable", "llm_analysis": "Semantically related guideline — review for relevance", "discovery_type": "semantic_discovery"}
            if m["guideline_scope"] == "company":
                analyzed_company.append(entry)
            else:
                analyzed_user.append(entry)

        results.append({
            "clause_type": clause.get("clause_type", "other"),
            "text_content": clause["text_content"],
            "summary": clause.get("summary", ""),
            "company_guideline_matches": analyzed_company,
            "user_guideline_matches": analyzed_user,
        })

    return results
