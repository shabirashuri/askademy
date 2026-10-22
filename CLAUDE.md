# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What we are building

**Smart Item Bank** is a prototype school assessment platform (the proving ground for the larger "akeb" project). It closes a loop between teaching material, a reusable question bank, assessments, and student demand:

1. Teacher logs in, creates a course and topics, uploads PDF/PPTX/DOCX material.
2. Backend extracts and chunks text; AI (LangChain + LangGraph) generates MCQs and short-answer questions; teacher reviews, edits, approves or rejects. Teachers can also write questions manually. Both land in the **same** `questions` table (`source = ai | manual`).
3. Teacher searches the bank, builds quizzes/exams from **approved** questions, and can export them to Word (python-docx, optional answer key).
4. Students take assigned quizzes (timer, autosave, MCQ auto-grading; optional AI grading of short answers with teacher override).
5. Students search course content/questions; every search is logged. A LangGraph analytics workflow clusters similar searches and produces teacher "suggested actions" (e.g. "students keep searching LEFT JOIN, generate 5 more questions") that feed back into the generation pipeline.

Source-of-truth documents in the repo root (read them before designing anything non-trivial):

- `Smart Item Bank Project Milestones.md` – four-milestone build plan.
- `Smart Item Bank Database Design.pdf` – full PostgreSQL schema, enums, indexes, design principles.
- `Smart_Item_Bank_Prototype_Explanation (1) (1).docx` – workflow, per-feature behaviour and transitions.
- `README.md`, `backend/README.md`, `frontend/README.md` – setup/run instructions.
- `memory/` – project investigation notes (e.g. the Supabase IPv6 / Alembic note).

## Milestones and current status

| # | Scope | Status |
|---|-------|--------|
| 1 | Foundation, JWT auth + roles, course/topic CRUD, enrollment, material upload, React shell, CI | **Complete** (not yet committed) |
| 2 | Text extraction, LangGraph generation pipeline with human-review interrupt, manual questions, review screen, bank search, LLM run logging | Not started (deps installed, schema modelled) |
| 3 | Quiz builder, Word export, student attempts, auto-grading, optional AI grading | Not started (schema modelled) |
| 4 | pgvector semantic search, search logging, insights/clustering, hardening, deployment | Not started (schema modelled) |

What exists today (Milestone 1):

- **Backend (`backend/app/`):** JWT login and `/auth/me` with login throttling; admin-managed users (`/users`); courses with ownership and student visibility; topics as a tree with ordering and soft delete; enrollments; material upload, download and soft delete with `StorageBackend` (`LocalStorage`). Error handling via `core/errors.py`. The admin seed script is `app/scripts/create_admin.py`.
- **Models:** the full item-bank schema in `app/models/item_bank.py`, including `Vector(1536)` chunks. Enum columns use `app.db.types.pg_enum`.
- **Migrations:** `0001`, `0002` (complete schema) and `0003` (`created_at` server defaults). Applied to Supabase.
- **Frontend (`frontend/src/`):** login, `AuthContext`, `ProtectedRoute` with roles, `AppShell`, dashboard, courses list and detail with a topic tree, the enrollment panel, the material uploader and list, and the admin Users page. Vitest tests cover the API client, route guards, login and upload validation.
- **Tests:** backend pytest suite (about 60 tests, slow because the database is remote) and frontend `npm test`.
- **Not built yet:** text extraction, AI generation, question bank, quizzes, attempts, search and insights. Students cannot see materials yet.
- **Known issue:** `alembic upgrade head` against the Supabase direct host works from this machine, but the IPv6 note in `memory/` still applies on IPv4-only networks.

## Tech stack

- Backend: Python 3.11+ (CI uses 3.12), FastAPI, Pydantic v2 / pydantic-settings, SQLAlchemy 2 (typed `Mapped[]` style), Alembic, psycopg 3, pgvector, passlib[bcrypt], python-jose, LangChain, LangGraph, python-docx/python-pptx/pypdf.
- Frontend: React 18, TypeScript, Vite 6, React Router 6, lucide-react, ESLint 9.
- Database: PostgreSQL on **Supabase** (pgvector available). `compose.yaml` offers a local `pgvector/pgvector:pg16` + API alternative; Docker is optional.

## Commands

Backend (run from `backend/`, venv active; a `.venv` also exists at repo root):

```bash
pip install -r requirements.txt        # or: pip install -e ".[dev]"
alembic upgrade head                   # apply migrations
alembic revision -m "..." --autogenerate   # new migration (review the output!)
uvicorn app.main:app --reload          # API on :8000, docs at /docs
pytest                                 # uses DATABASE_URL, sandboxed in a pytest_sandbox schema
ruff check .                           # line-length 100, rules E,F,I,UP
```

Frontend (run from `frontend/`):

```bash
npm ci
npm run dev        # http://localhost:5173
npm run lint
npm test           # Vitest + Testing Library (jsdom)
npm run build      # tsc -b && vite build
```

CI (`.github/workflows/ci.yml`) runs `ruff check .` + `pytest` for the backend (needs the `TEST_DATABASE_URL` repository secret) and `npm run lint`, `npm test` + `npm run build` for the frontend. Keep them green before finishing a task.

**Port note:** the API expects port 8000. On this machine port 8000 has been occupied by an unrelated ARTEMIS admin console (`apps.admin_console.server`) – check `ss -ltnp | grep :8000` and ask before killing anything; use `--port 8001` (and update `VITE_API_BASE_URL`/`CORS_ORIGINS`) if needed.

## Architecture and conventions

Backend layout under `backend/app/`: `api/v1/endpoints/` (thin routers, registered in `api/v1/api.py`, mounted at `/api/v1`), `core/` (settings, security), `db/` (Base, session), `models/`, `schemas/` (Pydantic request/response), `services/` (business logic and AI integrations). Keep routers thin; put logic in `services/`; never return ORM objects directly – use schemas.

Design rules from the database design doc – follow them:

- UUID primary keys everywhere; `created_at`/`updated_at` (timestamptz); `deleted_at` soft-delete on teacher-editable content (courses, topics, materials, questions, …). Always filter out soft-deleted rows in queries.
- **One question bank:** AI and manual questions share `questions`. Only `status = approved` questions may be added to assessments – enforce this in the service layer.
- **Everything hangs off course/topic:** materials, questions, assessments, searches carry `course_id` (and `topic_id`) for filtering and analytics.
- `search_logs` is append-only with minimal indexes; logging must never slow the student's search response (use a background task).
- LangGraph checkpoints live in the LangGraph Postgres checkpointer's own tables; the app only stores `generation_runs.langgraph_thread_id`. Use checkpointer + `interrupt` for the teacher-review pause. Record `model_name`, `prompt_version`, token counts and cost on every run.
- Keep prompt templates in one place (e.g. `app/services/ai/prompts/`), and the LLM provider configurable via settings. The embedding dimension is `EMBEDDING_DIMENSIONS = 1536` in `models/item_bank.py` – changing the embedding model means a migration.
- Roles: `admin`, `teacher`, `student`. Enforce authorization with FastAPI dependencies (current user + role guard) and check **ownership** (a teacher only touches their own courses; students only enrolled courses). Add permission tests for each protected endpoint.
- Schema changes: edit the model **and** add an Alembic migration; never edit an applied migration. Autogenerate output must be reviewed (pgvector, CITEXT, TSVECTOR, GIN/HNSW indexes need manual care).
- File uploads: validate extension, MIME type and size, store under `backend/storage/` (git-ignored) or object storage, record `content_hash` to detect duplicates, never trust the original filename for paths.
- Style: typed code, `from __future__ import annotations` in models, Ruff-clean, line length 100. Match surrounding code; don't add comments that restate the code.

Frontend: functional components with hooks, TypeScript strict, API calls go through `src/api/client.ts` (base URL from `VITE_API_BASE_URL`), pages in `src/pages/`, shared pieces in `src/components/`. Role-based routing (teacher vs student shell) is planned for milestone 1.

## Security and secrets

- Never commit `.env` files; only `.env.example` is tracked. `DATABASE_URL`, `JWT_SECRET_KEY`, LLM keys and the Supabase service-role key are secrets – never put them in frontend env vars, logs, or chat. `SUPABASE_URL`/`SUPABASE_KEY` are not used for the DB connection.
- Defaults in `config.py` (`jwt_secret_key`, DB password) are dev-only; fail fast or warn when `app_env` is not `development` and defaults are in use.
- Treat uploaded documents as untrusted input, including for prompt injection when fed to the LLM.

## Working agreements

- Check the milestone doc and design PDF before adding a table, endpoint or field; if code and docs disagree, flag it rather than silently picking one.
- Work milestone by milestone; Milestone 1 should be finished (auth, course/topic CRUD, upload, frontend login + dashboards) before starting AI features. Milestone 2 is the riskiest – design it carefully.
- Open decisions from the milestone doc still to settle with the user: LLM provider, file storage (local vs cloud), and student onboarding (self-signup vs teacher enrollment). Ask rather than assume.
- No Docker: the database is Supabase and uploaded files go to local disk (`backend/storage/`, behind a `StorageBackend` interface). Students are created by admins and enrolled by teachers (no self-signup).
- Add tests with new behaviour (pytest + `TestClient`). `tests/conftest.py` runs tests in a throwaway `pytest_sandbox` schema on the Supabase database with per-test rollback; it never touches `public` tables. The suite is slow (~75s) because of the remote DB.
- Enum columns must use `app.db.types.pg_enum` so values (`"teacher"`) match the migrations, not member names.
- Don't run destructive DB commands (`alembic downgrade`, drops, truncates) against Supabase without explicit confirmation.
- Commit only when asked.
