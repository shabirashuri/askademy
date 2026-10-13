# Backend

FastAPI service for Smart Item Bank.

## Requirements

- Python 3.11 or newer
- A Supabase project with its PostgreSQL database available
- Docker is not required to run the backend

Python packages are listed in [`requirements.txt`](requirements.txt). It installs the project and its development dependencies, including pytest and Ruff.

## Configure Supabase

In the Supabase dashboard, open your project and select **Connect** to get the PostgreSQL connection string. Copy the direct connection URI, or use the Session Pooler URI if your network cannot reach the direct database host.

Copy the repository environment template to `backend/.env`:

```bash
cp .env.example backend/.env
```

Set `DATABASE_URL` in `backend/.env` to the connection URI from Supabase. Use the `postgresql+psycopg://` scheme and append `?sslmode=require` (or `&sslmode=require` if the URI already has query parameters). Keep the Supabase database password private; URL-encode special characters in it.

`SUPABASE_URL` and `SUPABASE_KEY` are Supabase API credentials, not PostgreSQL credentials. SQLAlchemy and Alembic connect through `DATABASE_URL`; the current backend does not need the API key for database access. Do not put the Supabase service-role key in frontend environment variables or commit it.

## Run the backend

Create and activate a virtual environment, install dependencies, apply the database migration, and start FastAPI:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

The settings load `DATABASE_URL` from `backend/.env` when run from `backend/`.

The API is available at `http://localhost:8000`. Open `http://localhost:8000/docs` for interactive API documentation. The health endpoint is `http://localhost:8000/api/v1/health`.

Leave this terminal running. Use `Ctrl+C` to stop the API; the Supabase database remains available.

## Test and lint

With the virtual environment active, run from `backend/`:

```bash
pytest
ruff check .
```
