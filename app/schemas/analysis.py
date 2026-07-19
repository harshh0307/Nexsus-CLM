from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    extraction_queries: list[str] = []


class GuidelineUploadRequest(BaseModel):
    guidelines: list[dict]


class GuidelineMatchResponse(BaseModel):
    guideline_id: str
    standard_text: str
    risk_level: str
    similarity_score: float
    compliance_status: str
    llm_analysis: str
    discovery_type: str = "direct_match"


class ClauseResponse(BaseModel):
    clause_type: str
    text_content: str
    summary: str
    company_guideline_matches: list[GuidelineMatchResponse]
    user_guideline_matches: list[GuidelineMatchResponse]


class MismatchResponse(BaseModel):
    issue: str
    company_requirement: str
    user_requirement: str
    contract_says: str
    severity: str
    recommendation: str


class MissingClauseResponse(BaseModel):
    clause_type: str
    reason: str
    severity: str = "medium"
    recommendation: str = ""


class PartyConflictResponse(BaseModel):
    topic: str
    company_requires: str
    user_requires: str
    conflict_type: str
    resolution_suggestion: str
    severity: str


class CrossGapResponse(BaseModel):
    clause_type: str
    present_in: str
    missing_from: str
    company_text: str
    client_text: str
    severity: str
    recommendation: str


class TermConflictResponse(BaseModel):
    clause_type: str
    company_term: str
    client_term: str
    conflict_description: str
    severity: str
    resolution_suggestion: str


class ComparisonRequest(BaseModel):
    company_contract_id: str
    client_contract_id: str
    extraction_queries: list[str] = []


class AnalysisResponse(BaseModel):
    contract_id: str
    extracted_metadata: dict
    user_extracted_fields: dict
    clauses: list[ClauseResponse]
    mismatches: list[MismatchResponse]
    missing_clauses: list[MissingClauseResponse]
    party_conflicts: list[PartyConflictResponse]
    overall_risk_score: float
    risk_summary: str


class ComparisonResponse(BaseModel):
    company_contract_id: str
    client_contract_id: str
    company_analysis: AnalysisResponse
    client_analysis: AnalysisResponse
    cross_gaps: list[CrossGapResponse]
    term_conflicts: list[TermConflictResponse]
    overall_risk_score: float
    risk_summary: str
