# Contributing to NexusCLM

Thank you for considering contributing! This document outlines the guidelines.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Nexsus-CLM.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `docker exec nexus-clm-app-1 python3 -m pytest /app/tests/ -v`
6. Push and open a Pull Request

## Development Setup

```bash
docker compose up -d --build
```

The app reloads automatically on file changes. Frontend files in `frontend/` are live-synced via Docker volume mount. Python dependency changes require `docker compose build --no-cache app`.

## Code Style

- Python: follow PEP 8
- JavaScript: use ES6+ with `const`/`let`, no semicolons
- CSS: use BEM-like class naming
- No commented-out code — delete it
- No print/debug statements in production code
- Use `async`/`await` consistently

## Testing

Run the full test suite before submitting:

```bash
# Inside the running container
docker exec nexus-clm-app-1 python3 -m pytest /app/tests/ -v

# Legacy negative tests
docker exec nexus-clm-app-1 python3 /app/scripts/test_negative.py
```

All 31 tests should pass. If an analyze test times out, the LLM endpoint may be rate-limited — re-run later.

## Pull Request Checklist

- [ ] Tests pass
- [ ] New code has tests
- [ ] `.env` secrets are never committed
- [ ] The `.cmd` file rules are respected (ask before code changes, never ask for credentials, explain changes in depth)

## Project Structure

Key directories:
- `app/api/` — FastAPI route handlers
- `app/core/` — Business logic (LLM, embeddings, analysis)
- `app/db/` — Models and database setup
- `frontend/` — SPA served at `/ui`
- `tests/` — Pytest test suite
- `scripts/` — Legacy integration tests
- `docs/` — Guides (Power BI, etc.)
