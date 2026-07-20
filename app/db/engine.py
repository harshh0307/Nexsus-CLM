from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.config import settings
from app.db.models import *

engine = create_async_engine(settings.database_url, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


_ANALYTICS_VIEWS = [
    """
CREATE OR REPLACE VIEW v_risk_overview AS
SELECT ca.id AS analysis_id, ca.tenant_id, ca.contract_id, c.file_name, c.party,
       ca.overall_risk_score, ca.risk_summary, ca.created_at AS analysis_date,
       c.created_at AS contract_upload_date
FROM contract_analyses ca JOIN contracts c ON c.id = ca.contract_id
""",
    """
CREATE OR REPLACE VIEW v_clause_compliance AS
SELECT cgm.tenant_id, cc.clause_type, cgm.compliance_status, COUNT(*) AS match_count
FROM clause_guideline_matches cgm JOIN contract_clauses cc ON cc.id = cgm.clause_id
GROUP BY cgm.tenant_id, cc.clause_type, cgm.compliance_status
""",
    """
CREATE OR REPLACE VIEW v_guideline_coverage AS
SELECT ug.tenant_id, ug.id AS guideline_id, ug.guideline_type, ug.standard_text,
       ug.risk_level, ug.guideline_scope, COUNT(cgm.id) AS match_count,
       COUNT(DISTINCT cgm.compliance_status) AS distinct_statuses,
       COUNT(CASE WHEN cgm.compliance_status = 'non_compliant' THEN 1 END) AS violation_count,
       AVG(cgm.similarity_score) AS avg_similarity
FROM user_guidelines ug LEFT JOIN clause_guideline_matches cgm ON cgm.guideline_id = ug.id
GROUP BY ug.tenant_id, ug.id, ug.guideline_type, ug.standard_text, ug.risk_level, ug.guideline_scope
""",
    """
CREATE OR REPLACE VIEW v_missing_clause_frequency AS
SELECT tenant_id, clause_type, COUNT(*) AS frequency
FROM (SELECT ca.tenant_id, jsonb_array_elements(ca.missing_clauses::jsonb)->>'clause_type' AS clause_type
      FROM contract_analyses ca) sub
GROUP BY tenant_id, clause_type ORDER BY frequency DESC
""",
    """
CREATE OR REPLACE VIEW v_contract_summary AS
SELECT c.tenant_id, c.party, COUNT(DISTINCT c.id) AS contract_count,
       COUNT(DISTINCT cc.id) AS clause_count, AVG(ca.overall_risk_score) AS avg_risk_score,
       MAX(ca.overall_risk_score) AS max_risk_score, MIN(ca.overall_risk_score) AS min_risk_score,
       MIN(c.created_at) AS first_contract_date, MAX(c.created_at) AS last_contract_date
FROM contracts c LEFT JOIN contract_clauses cc ON cc.contract_id = c.id
LEFT JOIN contract_analyses ca ON ca.contract_id = c.id GROUP BY c.tenant_id, c.party
""",
    """
CREATE OR REPLACE VIEW v_audit_timeline AS
SELECT tenant_id, DATE(created_at) AS day, action, COUNT(*) AS action_count
FROM audit_logs GROUP BY tenant_id, DATE(created_at), action ORDER BY day DESC
""",
]


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        # Add party column to contracts table if it doesn't exist
        await conn.execute(text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS party VARCHAR DEFAULT 'company'"
        ))
        # Create analytics views for Power BI
        for stmt in _ANALYTICS_VIEWS:
            await conn.execute(text(stmt.strip()))


async def get_session():
    async with async_session() as session:
        yield session
