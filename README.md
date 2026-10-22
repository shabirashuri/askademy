# Smart Item Bank

Smart Item Bank is a school assessment platform for organizing course content, creating a reusable question bank, building quizzes, and helping teachers identify student learning needs.

## Technology

- **Frontend:** React, TypeScript, Vite, React Router
- **Backend:** FastAPI, Python 3.11+, Pydantic
- **Database:** Supabase-hosted PostgreSQL; pgvector is available for later semantic search
- **Data layer:** SQLAlchemy 2 and Alembic
- **AI pipeline:** LangChain and LangGraph dependencies are included for milestone 2
- **Local development:** FastAPI and Vite run on your machine; Supabase provides PostgreSQL, and Docker is not required.

## Project structure

```text
.
├── backend/
│   ├── alembic/                 # Database migrations
│   ├── app/
│   │   ├── api/v1/endpoints/    # Versioned HTTP endpoints
│   │   ├── core/                # Settings and security utilities
│   │   ├── db/                  # SQLAlchemy base and sessions
│   │   ├── models/              # Database models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # Business logic and integrations
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/                  # API client
│   │   ├── components/
│   │   ├── pages/
│   │   └── styles/
│   ├── index.html
│   ├── package.json
│   ├── README.md
│   └── vite.config.ts
└── .env.example
```

## Run locally

This project can run without Docker. You will need a Supabase project, Python, and Node.js.

### 1. Configure and start the backend

Get the PostgreSQL connection URI from **Supabase Dashboard → Connect**, then create the backend environment file and set `DATABASE_URL` to that URI:

```bash
cp .env.example backend/.env
```

`DATABASE_URL` is the database connection used by SQLAlchemy/Alembic. `SUPABASE_URL` and `SUPABASE_KEY` are API credentials and are not used for this PostgreSQL connection.

In the first terminal:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

The API will be at `http://localhost:8000` and its interactive docs at `http://localhost:8000/docs`. Keep this terminal open.

### 2. Start the frontend

In a second terminal, from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. The starter dashboard checks the local API health endpoint. Keep this terminal open too.

For detailed setup and run instructions, see the [backend README](backend/README.md) and [frontend README](frontend/README.md).

## Milestone 1 (complete)

Milestone 1 covers the foundation, which is now in place:

- **Accounts and roles:** JWT login, with admin, teacher and student roles. Administrators create accounts, and teachers enroll students in their courses. Passwords are reset from the Users page, and login attempts are throttled.
- **Courses and topics:** teachers create courses and organize topics into a tree with sub-topics and ordering. Students see only the courses they are enrolled in, read-only.
- **Material upload:** teachers upload PDF, PPTX and DOCX files to a topic. Files are validated, deduplicated per course and stored on local disk. They can be downloaded and soft-deleted.

Not yet built: text extraction, AI question generation, the question bank, quizzes, student attempts and search. These are milestones 2 to 4 in [the project plan](Smart%20Item%20Bank%20Project%20Milestones.md).

## Checks

Backend: `pytest` and `ruff check .` in `backend/`. Frontend: `npm test`, `npm run lint` and `npm run build` in `frontend/`. CI runs all of them. The backend job needs the `TEST_DATABASE_URL` repository secret.
