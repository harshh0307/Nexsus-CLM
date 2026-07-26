# NexusCLM

Autonomous post-signature contract intelligence engine. Upload contracts (PDF/DOCX), extract clauses with AI, compare against company and client guidelines, detect compliance gaps, and get risk scores — all powered by LLMs and vector search.

## Features

- **PDF & DOCX Upload** — Automatic text extraction via PyPDF and python-docx
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
- **Seed Guidelines** — 18 default company/user guidelines auto-created on registration
- **Custom Frontend** — Dark-themed SPA with glassmorphism UI served via FastAPI StaticFiles

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
| [python-docx](https://python-docx.readthedocs.io/) | DOCX text extraction |
| [Docker](https://www.docker.com/) | Containerized deployment |
| [Docker Compose](https://docs.docker.com/compose/) | Multi-service orchestration |
| [BCrypt](https://pypi.org/project/bcrypt/) | Password hashing |
| [python-jose](https://github.com/mpdavis/python-jose) | JWT token handling |

## Quick Start

### Prerequisites

- Docker Desktop (with WSL2)
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

This starts 4 services:

| Service | URL | Purpose |
|---|---|---|
| **App (API + Frontend)** | http://localhost:8000 | FastAPI server with SPA frontend at `/ui` |
| **Adminer** | http://localhost:8080 | Database admin UI |
| **API Docs** | http://localhost:8000/docs | Swagger/OpenAPI docs |

### 3. Use It

Open http://localhost:8000/ui/ in your browser, register a new account (or use the demo credentials below), then upload a PDF or DOCX contract.

**Demo credentials:**
- Email: `demo@nexusclm.com`
- Password: `demo123`

### API Usage

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
| POST | `/auth/register` | Register a new account (auto-seeds 18 guidelines) |
| POST | `/auth/login` | Login, returns JWT |
| POST | `/auth/forgot-password` | Request password reset |
| POST | `/auth/reset-password` | Reset password with token |
| GET | `/auth/me` | Get current user profile |

### Contracts (`/api/contracts`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/contracts/upload?party=company` | Upload PDF/DOCX contract |
| GET | `/api/contracts` | List all contracts |
| GET | `/api/contracts/{id}` | Get contract details with raw text preview |
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

## Frontend

A custom dark-themed SPA is served at `/ui` via FastAPI `StaticFiles`. Built with vanilla HTML, CSS, and modular JavaScript.

| Screen | Description |
|---|---|
| **Dashboard** | Contract/guideline counts, risk overview table, compliance stats |
| **Contracts** | Upload PDF/DOCX, view contract list, select for analysis |
| **Guidelines** | View/edit company and user guidelines (JSON) |
| **Analyze** | Pick a contract, run analysis, see clauses/missing/mismatches |
| **Compare** | Pick two contracts, detect cross-gaps and term conflicts |

Frontend source is in `frontend/` and live-syncs via Docker volume mount (no rebuild needed for static changes).

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

## Seed Guidelines

New users automatically receive 18 seed guidelines on registration:
- **12 Company guidelines** — indemnification, liability, termination, governing_law, confidentiality, data_protection, payment, warranty, insurance, force_majeure, anti_corruption, assignment
- **6 Client guidelines** — subset of the above for the client perspective

Guidelines are stored with 1536-dim embeddings for vector similarity matching (gracefully skips embedding if API is unavailable).

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
│   │   ├── contracts.py       # Contract upload (PDF/DOCX) and retrieval
│   │   ├── guidelines.py      # Guideline CRUD + semantic search
│   │   ├── analysis.py        # Analysis engine + comparison
│   │   └── analytics.py       # Power BI analytics endpoints
│   ├── core/
│   │   ├── llm.py             # LLM client with retry logic
│   │   ├── embedding.py       # Vector embedding generation
│   │   ├── clause_extractor.py # LLM clause extraction
│   │   ├── risk_analyzer.py   # pgvector similarity + compliance
│   │   ├── dynamic_schema.py  # Dynamic schema generation
│   │   └── seed_guidelines.py # Default guidelines on registration
│   ├── db/
│   │   ├── models.py          # 9 SQLModel table definitions
│   │   └── engine.py          # DB init + view creation
│   ├── schemas/
│   │   ├── auth.py            # Auth request/response models
│   │   ├── analysis.py        # Analysis/guideline response models
│   │   └── analytics.py       # Analytics response models
│   ├── security/
│   │   └── auth.py            # JWT + bcrypt + token management
│   ├── config.py              # Settings from .env
│   └── main.py                # FastAPI app + StaticFiles mount at /ui
├── frontend/
│   ├── index.html             # SPA shell (login + 5 screens)
│   ├── css/style.css          # Dark theme, glassmorphism, animations
│   └── js/
│       ├── api.js             # NexusAPI class (14 endpoints)
│       ├── auth.js            # Login/register + JWT management
│       └── screens.js         # Screen renderers + Toast helper
├── tests/
│   └── test_full_flow.py      # 31 pytest tests
├── scripts/
│   ├── test_phase3.py         # Full flow integration test
│   ├── test_negative.py       # 34 negative test cases
│   └── test_pgvector.py       # Vector search tests
├── docs/
│   └── power-bi-guide.md      # Power BI connection guide
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env
```

## Running Tests

```bash
# Run inside the running container
docker exec nexus-clm-app-1 python3 -m pytest /app/tests/ -v

# Run legacy negative tests
docker exec nexus-clm-app-1 python3 /app/scripts/test_negative.py
```

### Test Coverage (31 tests)

- **Auth** — register, duplicate, wrong password, no/invalid token, me endpoint, short password
- **Seed Guidelines** — 18 guidelines created, all have required fields
- **Contracts** — upload PDF, upload DOCX, invalid extension, invalid party, list, isolation, nonexistent, raw text, party field
- **Analyze** — full analysis pipeline, nonexistent contract
- **Compare** — cross-contract comparison, same contract rejection, invalid UUID
- **Guidelines** — upload company/user, list, empty rejection, delete, nonexistent delete
- **Cross-User Isolation** — user B cannot access user A's contracts
- **Health** — health check endpoint

## Database Tables

| Table | Purpose |
|---|---|
| `contracts` | Uploaded contracts with raw text and metadata |
| `contract_clauses` | Individual clauses with 1536-dim embeddings |
| `user_guidelines` | Guideline with company/user scope |
| `contract_analyses` | Analysis results with risk scores |
| `clause_guideline_matches` | Clause-to-guideline matches |
| `audit_logs` | Action audit trail |
| `users` | User accounts |
| `password_reset_tokens` | Password reset tokens |

## Stopping and Cleanup

```bash
# Stop containers
docker compose down

# Stop and delete all data (including volumes)
docker compose down -v
```

## License

MIT
