# NexusCLM

Autonomous post-signature contract intelligence engine. Upload contracts, extract clauses with AI, compare against company and client guidelines, detect compliance gaps, and get risk scores — all powered by LLMs and vector search.

## Features

- **PDF Contract Upload** — Automatic text extraction via PyPDF
- **LLM-Powered Analysis** — Extracts metadata, clauses, and compliance status using GPT-4o-mini
- **Clause Extraction** — Breaks contracts into 50+ legal clause types with vector embeddings
- **Guideline Matching** — Two-tier pgvector cosine similarity: direct match (>0.5) + semantic discovery (0.3-0.5)
- **Compliance Analysis** — Per-clause compliance status (compliant / non_compliant / partial / not_applicable)
- **Missing Clause Detection** — LLM checks against 50 expected clause types
- **Party Conflict Detection** — Finds contradictions between company and client requirements
- **Cross-Contract Comparison** — Side-by-side analysis with cross-gap and term conflict detection
- **Risk Scoring** — Weighted formula: 40% violations + 30% missing clauses + 30% conflicts
- **Power BI Integration** — 6 SQL views + 3 API endpoints for analytics dashboards
- **JWT Authentication** — Multi-tenant with bcrypt password hashing
- **314+ Pre-seeded Guidelines** — Across 49 legal categories

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.14 | Core language |
| [FastAPI](https://fastapi.tiangolo.com/) | Async web framework |
| [SQLAlchemy](https://www.sqlalchemy.org/) | Async ORM (via SQLModel) |
| [SQLModel](https://sqlmodel.tiangolo.com/) | SQLAlchemy + Pydantic integration |
| [PostgreSQL 16](https://www.postgresql.org/) | Primary database |
| [pgvector](https://github.com/pgvector/pgvector) | Vector similarity search (1536-dim embeddings) |
| [asyncpg](https://github.com/MagicStack/asyncpg) | Async PostgreSQL driver |
| [OpenAI SDK](https://github.com/openai/openai-python) | LLM API client (GitHub Models compatible) |
| [httpx](https://github.com/encode/httpx) | Async HTTP client for LLM calls |
| [PyPDF](https://github.com/py-pdf/pypdf) | PDF text extraction |
| [Docker](https://www.docker.com/) | Containerized deployment |
| [Docker Compose](https://docs.docker.com/compose/) | Multi-service orchestration |
| [BCrypt](https://pypi.org/project/bcrypt/) | Password hashing |
| [python-jose](https://github.com/mpdavis/python-jose) | JWT token handling |

## Quick Start

### Prerequisites

- Docker Desktop (with WSL2)
- Python 3.10+ (for running test scripts)
- A GitHub Personal Access Token (for [GitHub Models](https://github.com/marketplace/models))

### 1. Clone and Configure

```bash
git clone https://github.com/YOUR_USERNAME/nexus-clm.git
cd nexus-clm
```

Create a `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://nexus:nexus_secret@db:5432/nexus_clm
GITHUB_TOKEN=ghp_your_token_here
LLM_BASE_URL=https://models.inference.ai.azure.com
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_URL=https://models.inference.ai.azure.com
JWT_SECRET=your-secret-key-here
DEV_MODE=true
```

### 2. Start Everything

```bash
docker compose up -d --build
```

This starts 3 services:

| Service | URL | Purpose |
|---|---|---|
| **App** | http://localhost:8000 | FastAPI server |
| **Adminer** | http://localhost:8080 | Database admin UI |
| **API Docs** | http://localhost:8000/docs | Swagger/OpenAPI docs |

### 3. Use It

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"mypassword","name":"Your Name"}'

# Login (get JWT token)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"mypassword"}'
```

## API Endpoints

### Authentication (`/auth`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new account |
| POST | `/auth/login` | Login, returns JWT |
| POST | `/auth/forgot-password` | Request password reset |
| POST | `/auth/reset-password` | Reset password with token |
| GET | `/auth/me` | Get current user profile |

### Contracts (`/api/contracts`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/contracts/upload?party=company` | Upload PDF contract |
| GET | `/api/contracts` | List all contracts |
| GET | `/api/contracts/{id}` | Get contract details |
| POST | `/api/contracts/{id}/extract` | LLM metadata extraction |
| POST | `/api/contracts/{id}/analyze` | Full analysis pipeline |
| POST | `/api/contracts/compare` | Cross-contract comparison |

### Guidelines (`/api/guidelines`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/guidelines/company` | Upload company guidelines |
| POST | `/api/guidelines/user` | Upload client/user guidelines |
| GET | `/api/guidelines` | List all guidelines |
| DELETE | `/api/guidelines/{id}` | Delete a guideline |
| GET | `/api/guidelines/related/{id}` | Find semantically similar guidelines |

### Analytics (`/api/analytics`)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/analytics/dashboard` | Full dashboard (6 datasets) |
| GET | `/api/analytics/risk-trend` | Risk scores over time |
| GET | `/api/analytics/compliance` | Compliance breakdown |

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |

## Analysis Pipeline

When you analyze a contract, this 8-step pipeline runs:

```
1. Metadata Extraction (LLM)     → Title, parties, dates, amounts
2. User Field Extraction (LLM)   → Custom fields you specify
3. Clause Extraction (LLM)       → 50+ clause types identified
4. Embedding Generation           → 1536-dim vectors per clause
5. Guideline Matching (pgvector)  → Cosine similarity search
6. Compliance Analysis (LLM)     → Per-clause compliance status
7. Missing Clause Detection (LLM)→ Critical absent clauses
8. Risk Scoring (formula)         → 0.0 to 1.0 weighted score
```

## Power BI Integration

Port 5432 is exposed for direct PostgreSQL connection from Power BI.

| Setting | Value |
|---|---|
| Server | `localhost:5432` |
| Database | `nexus_clm` |
| Driver | PostgreSQL ODBC (psqlODBC) |

6 SQL views are auto-created:

| View | Data |
|---|---|
| `v_risk_overview` | Risk scores per analysis |
| `v_clause_compliance` | Compliance status by clause type |
| `v_guideline_coverage` | Guideline match rates |
| `v_missing_clause_frequency` | Most common missing clauses |
| `v_contract_summary` | Contract volume and risk by party |
| `v_audit_timeline` | Daily activity counts |

Full connection guide: `docs/power-bi-guide.md`

## Project Structure

```
nexus-clm/
├── app/
│   ├── api/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── contracts.py       # Contract upload and retrieval
│   │   ├── extraction.py      # LLM metadata extraction
│   │   ├── guidelines.py      # Guideline CRUD + semantic search
│   │   ├── analysis.py        # Analysis engine + comparison
│   │   └── analytics.py       # Power BI analytics endpoints
│   ├── core/
│   │   ├── llm.py             # LLM client with retry logic
│   │   ├── embedding.py       # Vector embedding generation
│   │   ├── clause_extractor.py # LLM clause extraction
│   │   ├── risk_analyzer.py   # pgvector similarity + compliance
│   │   └── dynamic_schema.py  # Dynamic schema generation
│   ├── db/
│   │   ├── models.py          # 9 SQLModel table definitions
│   │   ├── engine.py          # DB init + view creation
│   │   └── seed.py            # 314+ guideline seed data
│   ├── schemas/
│   │   ├── auth.py            # Auth request/response models
│   │   ├── analysis.py        # Analysis response models
│   │   └── analytics.py       # Analytics response models
│   ├── security/
│   │   └── auth.py            # JWT + bcrypt + token management
│   ├── config.py              # Settings from .env
│   └── main.py                # FastAPI app + router registration
├── scripts/
│   ├── test_phase3.py         # Full flow integration test
│   └── test_negative.py       # 34 negative test cases
├── docs/
│   └── power-bi-guide.md      # Power BI connection guide
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env
```

## Database Tables

| Table | Purpose |
|---|---|
| `contracts` | Uploaded contracts with raw text and metadata |
| `contract_clauses` | Individual clauses with 1536-dim embeddings |
| `corporate_guidelines` | Pre-seeded compliance guidelines |
| `user_guidelines` | User-uploaded guidelines (company/user scope) |
| `contract_analyses` | Analysis results with risk scores |
| `clause_guideline_matches` | Clause-to-guideline matches |
| `audit_logs` | Action audit trail |
| `users` | User accounts |
| `password_reset_tokens` | Password reset tokens |

## Stopping and Cleanup

```bash
# Stop containers
docker compose down

# Stop and delete all data
docker compose down -v
```

## License

MIT
