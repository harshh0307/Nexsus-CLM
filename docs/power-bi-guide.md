# Power BI Integration Guide

## Option 1: Direct PostgreSQL Connection (Recommended)

Power BI Desktop can connect directly to the NexusCLM PostgreSQL database using the SQL views.

### Prerequisites

1. Install **PostgreSQL ODBC Driver** (psqlODBC) from https://www.postgresql.org/ftp/odbc/versions/msi/
2. Power BI Desktop (free) from https://powerbi.microsoft.com/desktop/

### Connection Steps

1. Open **Power BI Desktop**
2. Click **Get Data** → **Other** → **ODBC** → **Connect**
3. Select the PostgreSQL ODBC driver (or create a new DSN)
4. Enter connection details:
   - **Server**: `localhost:5432`
   - **Database**: `nexus_clm`
   - **Username**: `nexus`
   - **Password**: `nexus_secret`
5. In the Navigator, select the `v_*` views:
   - `v_risk_overview` — Risk scores with timestamps and contract info
   - `v_clause_compliance` — Compliance status by clause type
   - `v_guideline_coverage` — Guideline match rates
   - `v_missing_clause_frequency` — Most common missing clauses
   - `v_contract_summary` — Contract volume by party
   - `v_audit_timeline` — Daily activity tracking

### DAX Measures (Useful for Dashboards)

**Average Risk Score:**
```dax
Avg Risk Score = AVERAGE(v_risk_overview[overall_risk_score])
```

**High Risk Count:**
```dax
High Risk Contracts = COUNTROWS(FILTER(v_risk_overview, v_risk_overview[overall_risk_score] > 0.7))
```

**Compliance Rate:**
```dax
Compliance Rate = DIVIDE(
    CALCULATE(COUNTROWS(v_clause_compliance), v_clause_compliance[compliance_status] = "compliant"),
    COUNTROWS(v_clause_compliance)
)
```

**Risk Trend:**
```dax
Risk Trend Line = AVERAGEX(
    VALUES(v_risk_overview[analysis_date]),
    CALCULATE(AVERAGE(v_risk_overview[overall_risk_score]))
)
```

### Suggested Dashboard Pages

1. **Risk Overview** — Cards (avg risk, high risk count, total contracts) + risk trend line chart
2. **Compliance Analysis** — Stacked bar chart of compliance status by clause type
3. **Guideline Coverage** — Table of guidelines with match count and violation rate
4. **Missing Clauses** — Bar chart of most frequent missing clause types
5. **Contract Summary** — Pie chart by party, avg risk comparison
6. **Activity Timeline** — Line chart of daily actions

---

## Option 2: REST API (Web Connector)

If direct DB access is not possible, use Power BI's **Web** data connector to query the analytics API.

### Endpoints

| Endpoint | Returns |
|---|---|
| `GET http://localhost:8000/api/analytics/dashboard` | All 6 datasets as JSON |
| `GET http://localhost:8000/api/analytics/risk-trend` | Risk scores over time |
| `GET http://localhost:8000/api/analytics/compliance` | Compliance breakdown |

### Power Query (M) Example

```
let
    Source = Json.Document(Web.Contents("http://localhost:8000/api/analytics/dashboard", [
        Headers=[Authorization="Bearer YOUR_JWT_TOKEN"]
    ])),
    RiskOverview = Table.FromList(Source[risk_overview], Splitter.SplitByNothing()),
    Expanded = Table.ExpandRecordColumn(RiskOverview, "Column1", {
        "analysis_id", "contract_id", "file_name", "party",
        "overall_risk_score", "risk_summary", "analysis_date", "contract_upload_date"
    })
in
    Expanded
```

> **Note**: You need a valid JWT token for API access. Get one via `POST /auth/login`.

---

## View Definitions Reference

The analytics views are created automatically on app startup. Full SQL definitions in `init.sql` and `app/db/engine.py`.

| View | Columns | Filter |
|---|---|---|
| `v_risk_overview` | analysis_id, contract_id, file_name, party, overall_risk_score, risk_summary, analysis_date, contract_upload_date | tenant_id |
| `v_clause_compliance` | clause_type, compliance_status, match_count | tenant_id |
| `v_guideline_coverage` | guideline_id, guideline_type, standard_text, risk_level, guideline_scope, match_count, distinct_statuses, violation_count, avg_similarity | tenant_id |
| `v_missing_clause_frequency` | clause_type, frequency | tenant_id |
| `v_contract_summary` | party, contract_count, clause_count, avg_risk_score, max_risk_score, min_risk_score, first_contract_date, last_contract_date | tenant_id |
| `v_audit_timeline` | day, action, action_count | tenant_id |

All views are scoped by `tenant_id` (each user sees only their own data).
