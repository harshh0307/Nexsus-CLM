from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class RiskOverviewItem(BaseModel):
    analysis_id: str
    contract_id: str
    file_name: str
    party: str
    overall_risk_score: float
    risk_summary: str
    analysis_date: datetime
    contract_upload_date: datetime


class ClauseComplianceItem(BaseModel):
    clause_type: str
    compliance_status: str
    match_count: int


class GuidelineCoverageItem(BaseModel):
    guideline_id: str
    guideline_type: str
    standard_text: str
    risk_level: str
    guideline_scope: str
    match_count: int
    distinct_statuses: int
    violation_count: int
    avg_similarity: float | None = None


class MissingClauseFrequencyItem(BaseModel):
    clause_type: str
    frequency: int


class ContractSummaryItem(BaseModel):
    party: str
    contract_count: int
    clause_count: int
    avg_risk_score: float | None = None
    max_risk_score: float | None = None
    min_risk_score: float | None = None
    first_contract_date: datetime | None = None
    last_contract_date: datetime | None = None


class AuditTimelineItem(BaseModel):
    day: date
    action: str
    action_count: int


class DashboardResponse(BaseModel):
    risk_overview: list[RiskOverviewItem]
    clause_compliance: list[ClauseComplianceItem]
    guideline_coverage: list[GuidelineCoverageItem]
    missing_clause_frequency: list[MissingClauseFrequencyItem]
    contract_summary: list[ContractSummaryItem]
    audit_timeline: list[AuditTimelineItem]
