from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.db.engine import get_session
from app.db.models import User
from app.schemas.analytics import (
    AuditTimelineItem,
    ClauseComplianceItem,
    ContractSummaryItem,
    DashboardResponse,
    GuidelineCoverageItem,
    MissingClauseFrequencyItem,
    RiskOverviewItem,
)
from app.security.auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    tenant_id = str(user.id)

    rows = await session.execute(
        text("SELECT analysis_id, contract_id, file_name, party, overall_risk_score, risk_summary, analysis_date, contract_upload_date FROM v_risk_overview WHERE tenant_id = :tid ORDER BY analysis_date DESC"),
        {"tid": tenant_id}
    )
    risk_overview = [RiskOverviewItem(**r._mapping) for r in rows]

    rows = await session.execute(
        text("SELECT clause_type, compliance_status, match_count FROM v_clause_compliance WHERE tenant_id = :tid ORDER BY match_count DESC"),
        {"tid": tenant_id}
    )
    clause_compliance = [ClauseComplianceItem(**r._mapping) for r in rows]

    rows = await session.execute(
        text("SELECT guideline_id, guideline_type, standard_text, risk_level, guideline_scope, match_count, distinct_statuses, violation_count, avg_similarity FROM v_guideline_coverage WHERE tenant_id = :tid ORDER BY match_count DESC"),
        {"tid": tenant_id}
    )
    guideline_coverage = [GuidelineCoverageItem(**r._mapping) for r in rows]

    rows = await session.execute(
        text("SELECT clause_type, frequency FROM v_missing_clause_frequency WHERE tenant_id = :tid ORDER BY frequency DESC"),
        {"tid": tenant_id}
    )
    missing_clause_frequency = [MissingClauseFrequencyItem(**r._mapping) for r in rows]

    rows = await session.execute(
        text("SELECT party, contract_count, clause_count, avg_risk_score, max_risk_score, min_risk_score, first_contract_date, last_contract_date FROM v_contract_summary WHERE tenant_id = :tid"),
        {"tid": tenant_id}
    )
    contract_summary = [ContractSummaryItem(**r._mapping) for r in rows]

    rows = await session.execute(
        text("SELECT day, action, action_count FROM v_audit_timeline WHERE tenant_id = :tid ORDER BY day DESC, action_count DESC"),
        {"tid": tenant_id}
    )
    audit_timeline = [AuditTimelineItem(**r._mapping) for r in rows]

    return DashboardResponse(
        risk_overview=risk_overview,
        clause_compliance=clause_compliance,
        guideline_coverage=guideline_coverage,
        missing_clause_frequency=missing_clause_frequency,
        contract_summary=contract_summary,
        audit_timeline=audit_timeline,
    )


@router.get("/risk-trend", response_model=list[RiskOverviewItem])
async def get_risk_trend(
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    rows = await session.execute(
        text("SELECT analysis_id, contract_id, file_name, party, overall_risk_score, risk_summary, analysis_date, contract_upload_date FROM v_risk_overview WHERE tenant_id = :tid ORDER BY analysis_date ASC"),
        {"tid": str(user.id)}
    )
    return [RiskOverviewItem(**r._mapping) for r in rows]


@router.get("/compliance", response_model=list[ClauseComplianceItem])
async def get_compliance(
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    rows = await session.execute(
        text("SELECT clause_type, compliance_status, match_count FROM v_clause_compliance WHERE tenant_id = :tid ORDER BY clause_type, compliance_status"),
        {"tid": str(user.id)}
    )
    return [ClauseComplianceItem(**r._mapping) for r in rows]
