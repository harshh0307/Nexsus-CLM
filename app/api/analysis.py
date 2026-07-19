import uuid
from datetime import datetime, timezone

_naive_utc = lambda: datetime.now(timezone.utc).replace(tzinfo=None)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.core.clause_extractor import extract_clauses
from app.core.dynamic_schema import extract_fields, generate_schema
from app.core.embedding import generate_embeddings
from app.core.llm import extract_json
from app.core.risk_analyzer import analyze_clauses
from app.db.engine import get_session
from app.db.models import (
    AuditLog,
    ClauseGuidelineMatch,
    Contract,
    ContractAnalysis,
    ContractClause,
    User,
    UserGuideline,
)
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    ComparisonRequest,
    ComparisonResponse,
    CrossGapResponse,
    TermConflictResponse,
)
from app.security.auth import get_current_user

router = APIRouter(prefix="/api/contracts", tags=["analysis"])

CRITICAL_CLAUSE_TYPES = [
    "indemnification", "liability", "termination", "governing_law",
    "confidentiality", "payment", "data_protection", "warranty",
]

_MISSING_CLAUSE_PROMPT = """You are a legal contract analyst. Analyze this contract and identify which important legal clauses are MISSING.

Contract text:
{contract_text}

For this type of contract ({contract_type}), the following clause types are typically expected:
{clause_types}

Analyze the contract and identify which of these clause types are genuinely missing (not just mentioned in passing, but not actually present as a substantive provision).

Return JSON:
{{
  "missing_clauses": [
    {{
      "clause_type": "type name",
      "reason": "Why this clause is important for this contract type",
      "severity": "critical|high|medium|low",
      "recommendation": "What should be added"
    }}
  ]
}}

Rules:
- Only include clauses that are TRULY missing, not just briefly mentioned
- Consider the contract type when determining importance
- A software license MUST have: payment, termination, governing_law, warranty, liability, indemnification, confidentiality, intellectual_property
- Return ONLY valid JSON with no markdown or explanation."""

_PARTY_CONFLICT_PROMPT = """You are a legal compliance analyzer. Two parties (Company and User/Client) each have their own guidelines for contract terms. Identify where their requirements CONFLICT with each other.

Company guidelines:
{company_guidelines}

User guidelines:
{user_guidelines}

Analyze whether any company guideline contradicts or conflicts with any user guideline on the same topic.

Return JSON:
{{
  "conflicts": [
    {{
      "topic": "area of conflict (e.g., indemnification, liability cap, termination notice)",
      "company_requires": "what the company guideline says",
      "user_requires": "what the user guideline says",
      "conflict_type": "direct_contradiction|different_requirements|missing_from_one_party",
      "resolution_suggestion": "suggested middle ground or resolution",
      "severity": "critical|high|medium|low"
    }}
  ]
}}

Rules:
- Only report genuine conflicts, not just different wording for the same thing
- Focus on substantive differences in requirements
- Return ONLY valid JSON with no markdown or explanation"""

_TERM_CONFLICT_PROMPT = """You are a legal contract comparison analyzer. Two parties have contracts with the same clause type but potentially different terms.

Company contract "{clause_type}" clause:
{company_text}

Client contract "{clause_type}" clause:
{client_text}

Identify any contradictions, conflicts, or significant differences between these two versions of the same clause type.

Return JSON:
{{
  "conflicts": [
    {{
      "description": "What is contradictory or significantly different between the two versions",
      "severity": "critical|high|medium|low",
      "resolution_suggestion": "Suggested middle ground or resolution"
    }}
  ]
}}

Rules:
- Focus on substantive differences, not minor wording variations
- If the clauses are essentially the same, return an empty conflicts list
- Return ONLY valid JSON with no markdown or explanation"""


async def _run_full_analysis(
    contract: Contract,
    extraction_queries: list[str],
    user: User,
    session,
) -> AnalysisResponse:
    """Core analysis pipeline. Used by both single analysis and comparison endpoints."""
    # 1. Extract metadata
    try:
        schema = await generate_schema(contract.raw_text, [])
        extracted_metadata = await extract_fields(contract.raw_text, schema)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Metadata extraction failed: {str(e)}")

    # 2. Extract user-requested fields
    user_extracted_fields = {}
    if extraction_queries:
        try:
            user_extracted_fields = await extract_fields(contract.raw_text, {"fields": extraction_queries})
        except Exception as e:
            user_extracted_fields = {"error": str(e)}

    # 3. Extract clauses
    try:
        clauses = await extract_clauses(contract.raw_text)
    except Exception as e:
        clauses = []

    # 4. Generate embeddings
    clause_texts = [c["text_content"] for c in clauses if c.get("text_content")]
    clause_embeddings = []
    if clause_texts:
        try:
            clause_embeddings = await generate_embeddings(clause_texts)
        except Exception as e:
            clause_embeddings = [[] for _ in clause_texts]

    # 5. Analyze clauses against guidelines
    analyzed_clauses = []
    if clauses and clause_embeddings:
        try:
            analyzed_clauses = await analyze_clauses(clauses, clause_embeddings, str(user.id), session)
        except Exception as e:
            analyzed_clauses = [
                {
                    "clause_type": c.get("clause_type", "other"),
                    "text_content": c["text_content"],
                    "summary": c.get("summary", ""),
                    "company_guideline_matches": [],
                    "user_guideline_matches": [],
                }
                for c in clauses
            ]

    # 6. LLM-powered missing clause detection
    try:
        contract_type = extracted_metadata.get("agreement_title", "contract")
        all_clause_types = [
            "indemnification", "liability", "termination", "governing_law",
            "confidentiality", "payment", "renewal", "data_protection",
            "intellectual_property", "insurance", "force_majeure", "warranty",
            "sla", "audit", "anti_corruption", "assignment", "subcontracting",
            "non_compete", "non_solicitation", "entire_agreement", "amendments",
            "publicity", "notices", "export_control", "third_party", "waiver",
            "severability", "survival", "independent_contractor", "counterparts",
            "further_assurances", "time_essence", "cumulative_remedies",
            "legal_fees", "set_off", "delivery", "training", "support",
            "disaster_recovery", "transition", "records_retention", "sanctions",
            "diversity", "data_security", "compliance", "right_to_use",
            "benchmarks", "pricing", "scope",
        ]
        missing_result = await extract_json(
            "You are a legal contract clause analysis system.",
            _MISSING_CLAUSE_PROMPT.format(
                contract_text=contract.raw_text[:12000],
                contract_type=contract_type,
                clause_types=", ".join(all_clause_types),
            )
        )
        missing_clauses = missing_result.get("missing_clauses", [])
    except Exception:
        present_types = {c["clause_type"] for c in analyzed_clauses}
        all_types = [
            "indemnification", "liability", "termination", "governing_law",
            "confidentiality", "payment", "data_protection", "intellectual_property",
            "insurance", "warranty", "force_majeure", "sla", "audit",
        ]
        missing_clauses = [
            {"clause_type": t, "reason": f"Contract does not contain a {t.replace('_', ' ')} clause", "severity": "medium", "recommendation": f"Add a {t.replace('_', ' ')} clause"}
            for t in all_types if t not in present_types
        ]

    # 7. Party conflict detection
    party_conflicts = []
    try:
        guids_stmt = select(UserGuideline).where(UserGuideline.tenant_id == str(user.id))
        all_guidelines = (await session.execute(guids_stmt)).scalars().all()

        company_guidelines = [g for g in all_guidelines if g.guideline_scope == "company"]
        user_guidelines = [g for g in all_guidelines if g.guideline_scope == "user"]

        if company_guidelines and user_guidelines:
            company_text = "\n".join([f"- [{g.guideline_type}] {g.standard_text} (risk: {g.risk_level})" for g in company_guidelines[:20]])
            user_text = "\n".join([f"- [{g.guideline_type}] {g.standard_text} (risk: {g.risk_level})" for g in user_guidelines[:20]])

            conflict_result = await extract_json(
                "You are a legal compliance analyzer comparing two parties' requirements.",
                _PARTY_CONFLICT_PROMPT.format(
                    company_guidelines=company_text,
                    user_guidelines=user_text,
                )
            )
            party_conflicts = conflict_result.get("conflicts", [])
    except Exception:
        party_conflicts = []

    # 8. Save clause records and matches
    for i, clause_data in enumerate(analyzed_clauses):
        clause_record = ContractClause(
            contract_id=contract.id,
            tenant_id=str(user.id),
            clause_type=clause_data["clause_type"],
            text_content=clause_data["text_content"],
            embedding=clause_embeddings[i] if i < len(clause_embeddings) else None,
        )
        session.add(clause_record)
        await session.flush()

        for match in clause_data.get("company_guideline_matches", []) + clause_data.get("user_guideline_matches", []):
            match_record = ClauseGuidelineMatch(
                clause_id=clause_record.id,
                guideline_id=uuid.UUID(match["guideline_id"]),
                tenant_id=str(user.id),
                similarity_score=match["similarity_score"],
                compliance_status=match.get("compliance_status", "not_applicable"),
                llm_analysis=match.get("llm_analysis", ""),
            )
            session.add(match_record)

    # 9. Detect mismatches and calculate risk
    mismatches = _detect_mismatches(analyzed_clauses)
    risk_score = _calculate_risk_score(analyzed_clauses, missing_clauses, party_conflicts)
    risk_summary = _generate_risk_summary(risk_score, mismatches, missing_clauses, analyzed_clauses, party_conflicts)

    # 10. Save analysis record
    analysis = ContractAnalysis(
        contract_id=contract.id,
        tenant_id=str(user.id),
        extraction_queries=extraction_queries,
        extracted_fields=extracted_metadata,
        user_extracted_fields=user_extracted_fields,
        mismatches=mismatches + [{"type": "party_conflict", **c} for c in party_conflicts],
        missing_clauses=missing_clauses,
        overall_risk_score=risk_score,
        risk_summary=risk_summary,
    )
    session.add(analysis)

    contract.extracted_metadata = extracted_metadata
    contract.status = "analyzed"
    contract.updated_at = _naive_utc()

    return AnalysisResponse(
        contract_id=str(contract.id),
        extracted_metadata=extracted_metadata,
        user_extracted_fields=user_extracted_fields,
        clauses=[_clause_to_response(c) for c in analyzed_clauses],
        mismatches=[_mismatch_to_response(m) for m in mismatches],
        missing_clauses=[_missing_to_response(m) for m in missing_clauses],
        party_conflicts=[_conflict_to_response(c) for c in party_conflicts],
        overall_risk_score=risk_score,
        risk_summary=risk_summary,
    )


def _detect_cross_gaps(
    company_clauses: list[dict],
    client_clauses: list[dict],
) -> list[CrossGapResponse]:
    """Detect clause types present in one contract but missing from the other."""
    company_types = {c["clause_type"] for c in company_clauses}
    client_types = {c["clause_type"] for c in client_clauses}

    gaps = []

    # Present in company, missing from client
    for t in company_types - client_types:
        clause = next((c for c in company_clauses if c["clause_type"] == t), None)
        gaps.append(CrossGapResponse(
            clause_type=t,
            present_in="company",
            missing_from="client",
            company_text=clause["text_content"][:300] if clause else "",
            client_text="",
            severity="high" if t in CRITICAL_CLAUSE_TYPES else "medium",
            recommendation=f"Client contract should include a {t.replace('_', ' ')} clause to match company requirements",
        ))

    # Present in client, missing from company
    for t in client_types - company_types:
        clause = next((c for c in client_clauses if c["clause_type"] == t), None)
        gaps.append(CrossGapResponse(
            clause_type=t,
            present_in="client",
            missing_from="company",
            company_text="",
            client_text=clause["text_content"][:300] if clause else "",
            severity="high" if t in CRITICAL_CLAUSE_TYPES else "medium",
            recommendation=f"Company contract should include a {t.replace('_', ' ')} clause to address client expectations",
        ))

    return gaps


async def _detect_term_conflicts(
    company_clauses: list[dict],
    client_clauses: list[dict],
) -> list[TermConflictResponse]:
    """For matching clause types, use LLM to find contradictory terms."""
    company_types = {c["clause_type"] for c in company_clauses}
    client_types = {c["clause_type"] for c in client_clauses}
    matching_types = company_types & client_types

    conflicts = []
    for clause_type in matching_types:
        company_clause = next(c for c in company_clauses if c["clause_type"] == clause_type)
        client_clause = next(c for c in client_clauses if c["clause_type"] == clause_type)

        company_text = company_clause["text_content"][:2000]
        client_text = client_clause["text_content"][:2000]

        # Skip if texts are very short or identical
        if len(company_text) < 50 or len(client_text) < 50:
            continue
        if company_text.strip() == client_text.strip():
            continue

        try:
            result = await extract_json(
                "You are a legal contract comparison analyzer.",
                _TERM_CONFLICT_PROMPT.format(
                    clause_type=clause_type,
                    company_text=company_text,
                    client_text=client_text,
                )
            )
            for c in result.get("conflicts", []):
                conflicts.append(TermConflictResponse(
                    clause_type=clause_type,
                    company_term=company_text[:300],
                    client_term=client_text[:300],
                    conflict_description=c.get("description", ""),
                    severity=c.get("severity", "medium"),
                    resolution_suggestion=c.get("resolution_suggestion", ""),
                ))
        except Exception:
            continue

    return conflicts


@router.post("/{contract_id}/analyze", response_model=AnalysisResponse)
async def analyze_contract(
    contract_id: uuid.UUID,
    body: AnalysisRequest,
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contract has no raw text to analyze")

    result = await _run_full_analysis(contract, body.extraction_queries, user, session)

    audit = AuditLog(
        tenant_id=str(user.id),
        contract_id=contract.id,
        action="contract_analyzed",
        performed_by=str(user.id),
        details={
            "clauses_count": len(result.clauses),
            "mismatches_count": len(result.mismatches),
            "missing_clauses_count": len(result.missing_clauses),
            "party_conflicts_count": len(result.party_conflicts),
            "risk_score": result.overall_risk_score,
        },
    )
    session.add(audit)
    await session.commit()
    await session.refresh(contract)

    return result


@router.post("/compare", response_model=ComparisonResponse)
async def compare_contracts(
    body: ComparisonRequest,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    # Validate UUIDs
    try:
        company_uuid = uuid.UUID(body.company_contract_id)
        client_uuid = uuid.UUID(body.client_contract_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid contract ID format")

    # Load both contracts
    company_stmt = select(Contract).where(
        Contract.id == company_uuid,
        Contract.tenant_id == str(user.id),
    )
    company_contract = (await session.execute(company_stmt)).scalar_one_or_none()
    if not company_contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company contract not found")

    if company_uuid == client_uuid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot compare a contract with itself")

    client_stmt = select(Contract).where(
        Contract.id == client_uuid,
        Contract.tenant_id == str(user.id),
    )
    client_contract = (await session.execute(client_stmt)).scalar_one_or_none()
    if not client_contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client contract not found")

    if not company_contract.raw_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company contract has no raw text")
    if not client_contract.raw_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client contract has no raw text")

    # Run full analysis on each
    company_analysis = await _run_full_analysis(company_contract, body.extraction_queries, user, session)
    client_analysis = await _run_full_analysis(client_contract, body.extraction_queries, user, session)

    # Cross-gap detection
    cross_gaps = _detect_cross_gaps(
        [c.dict() for c in company_analysis.clauses],
        [c.dict() for c in client_analysis.clauses],
    )

    # Term conflict detection
    term_conflicts = await _detect_term_conflicts(
        [c.dict() for c in company_analysis.clauses],
        [c.dict() for c in client_analysis.clauses],
    )

    # Combined risk score
    all_scores = [
        company_analysis.overall_risk_score,
        client_analysis.overall_risk_score,
    ]
    gap_penalty = min(1.0, len(cross_gaps) * 0.05)
    conflict_penalty = min(1.0, len(term_conflicts) * 0.1)
    overall_risk = round(min(1.0, (sum(all_scores) / len(all_scores)) + gap_penalty + conflict_penalty), 2)

    # Risk summary
    parts = []
    if overall_risk > 0.7:
        parts.append(f"HIGH RISK ({overall_risk*100:.0f}%): Significant issues in both contracts.")
    elif overall_risk > 0.4:
        parts.append(f"MODERATE RISK ({overall_risk*100:.0f}%): Some compliance concerns across both contracts.")
    elif overall_risk > 0.1:
        parts.append(f"LOW RISK ({overall_risk*100:.0f}%): Minor issues detected.")
    else:
        parts.append(f"LOW RISK ({overall_risk*100:.0f}%): Both contracts appear largely compliant.")

    if cross_gaps:
        critical_gaps = [g for g in cross_gaps if g.severity == "high"]
        parts.append(f"{len(cross_gaps)} clause gaps found ({len(critical_gaps)} critical).")
    if term_conflicts:
        critical_conflicts = [c for c in term_conflicts if c.severity in ("critical", "high")]
        parts.append(f"{len(term_conflicts)} term conflicts found ({len(critical_conflicts)} critical).")
    parts.append(f"Company: {company_analysis.overall_risk_score*100:.0f}% risk. Client: {client_analysis.overall_risk_score*100:.0f}% risk.")

    risk_summary = " ".join(parts)

    # Save comparison as analysis records
    comparison_audit = AuditLog(
        tenant_id=str(user.id),
        action="contracts_compared",
        performed_by=str(user.id),
        details={
            "company_contract_id": body.company_contract_id,
            "client_contract_id": body.client_contract_id,
            "cross_gaps_count": len(cross_gaps),
            "term_conflicts_count": len(term_conflicts),
            "overall_risk_score": overall_risk,
        },
    )
    session.add(comparison_audit)
    await session.commit()

    return ComparisonResponse(
        company_contract_id=body.company_contract_id,
        client_contract_id=body.client_contract_id,
        company_analysis=company_analysis,
        client_analysis=client_analysis,
        cross_gaps=cross_gaps,
        term_conflicts=term_conflicts,
        overall_risk_score=overall_risk,
        risk_summary=risk_summary,
    )


def _detect_mismatches(analyzed_clauses: list[dict]) -> list[dict]:
    mismatches = []
    for clause in analyzed_clauses:
        company_violations = [
            m for m in clause.get("company_guideline_matches", [])
            if m.get("compliance_status") == "non_compliant"
        ]
        user_violations = [
            m for m in clause.get("user_guideline_matches", [])
            if m.get("compliance_status") == "non_compliant"
        ]
        if company_violations or user_violations:
            for m in company_violations:
                mismatches.append({
                    "issue": f"{clause['clause_type']} violates company guideline",
                    "company_requirement": m["standard_text"],
                    "user_requirement": next(
                        (um["standard_text"] for um in user_violations if um["guideline_type"] == m["guideline_type"]),
                        "No matching user guideline"
                    ),
                    "contract_says": clause["text_content"][:200],
                    "severity": m.get("risk_level", "medium"),
                    "recommendation": f"Review {clause['clause_type']} clause for compliance",
                })
            for m in user_violations:
                if not any(cm["guideline_type"] == m["guideline_type"] for cm in company_violations):
                    mismatches.append({
                        "issue": f"{clause['clause_type']} violates user guideline",
                        "company_requirement": "No matching company guideline",
                        "user_requirement": m["standard_text"],
                        "contract_says": clause["text_content"][:200],
                        "severity": m.get("risk_level", "medium"),
                        "recommendation": f"Review {clause['clause_type']} clause for user compliance",
                    })
    return mismatches


def _calculate_risk_score(
    analyzed_clauses: list[dict],
    missing_clauses: list[dict],
    party_conflicts: list[dict],
) -> float:
    scores = []

    total_matches = 0
    violations = 0
    for clause in analyzed_clauses:
        for m in clause.get("company_guideline_matches", []) + clause.get("user_guideline_matches", []):
            if m.get("similarity_score", 0) > 0.5:
                total_matches += 1
                if m.get("compliance_status") == "non_compliant":
                    violations += 1
    violation_score = violations / max(total_matches, 1)
    scores.append(("violations", violation_score, 0.4))

    critical_missing = len([m for m in missing_clauses if m.get("severity") == "critical"])
    high_missing = len([m for m in missing_clauses if m.get("severity") == "high"])
    missing_score = min(1.0, (critical_missing * 0.3 + high_missing * 0.15))
    scores.append(("missing", missing_score, 0.3))

    critical_conflicts = len([c for c in party_conflicts if c.get("severity") == "critical"])
    high_conflicts = len([c for c in party_conflicts if c.get("severity") == "high"])
    conflict_score = min(1.0, (critical_conflicts * 0.35 + high_conflicts * 0.2))
    scores.append(("conflicts", conflict_score, 0.3))

    total = sum(score * weight for _, score, weight in scores)
    return round(min(1.0, total), 2)


def _generate_risk_summary(
    risk_score: float,
    mismatches: list[dict],
    missing_clauses: list[dict],
    analyzed_clauses: list[dict],
    party_conflicts: list[dict],
) -> str:
    parts = []

    if risk_score > 0.7:
        parts.append(f"HIGH RISK ({risk_score*100:.0f}%): This contract has significant compliance issues.")
    elif risk_score > 0.4:
        parts.append(f"MODERATE RISK ({risk_score*100:.0f}%): This contract has some compliance concerns.")
    elif risk_score > 0.1:
        parts.append(f"LOW RISK ({risk_score*100:.0f}%): Minor compliance issues detected.")
    else:
        parts.append(f"LOW RISK ({risk_score*100:.0f}%): Contract appears largely compliant.")

    high_risk = [m for m in mismatches if m.get("severity") == "high"]
    if high_risk:
        parts.append(f"{len(high_risk)} high-severity guideline violations found.")

    critical_missing = [m for m in missing_clauses if m.get("severity") == "critical"]
    high_missing = [m for m in missing_clauses if m.get("severity") == "high"]
    if critical_missing:
        parts.append(f"{len(critical_missing)} CRITICAL clauses missing: {', '.join(m['clause_type'] for m in critical_missing[:5])}.")
    if high_missing:
        parts.append(f"{len(high_missing)} important clauses missing: {', '.join(m['clause_type'] for m in high_missing[:5])}.")

    if party_conflicts:
        parts.append(f"{len(party_conflicts)} conflicts detected between company and user guidelines.")

    parts.append(f"{len(analyzed_clauses)} clauses analyzed from the contract.")

    return " ".join(parts)


def _clause_to_response(clause: dict) -> dict:
    return {
        "clause_type": clause["clause_type"],
        "text_content": clause["text_content"],
        "summary": clause.get("summary", ""),
        "company_guideline_matches": clause.get("company_guideline_matches", []),
        "user_guideline_matches": clause.get("user_guideline_matches", []),
    }


def _mismatch_to_response(mismatch: dict) -> dict:
    return mismatch


def _missing_to_response(missing: dict) -> dict:
    return missing


def _conflict_to_response(conflict: dict) -> dict:
    return conflict
