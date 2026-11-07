# Internship Tracker

One place for every internship application: a Kanban board, deadlines, follow-ups,
interview dates, contacts, notes and status history.

- **Frontend:** React 18 + Vite (`frontend/`)
- **Backend:** FastAPI + SQLAlchemy + Alembic (`backend/`)
- **Database:** PostgreSQL 16 in Docker; SQLite for quick local runs and tests (`DATABASE_URL`)
- **Docker:** `docker-compose.yml` runs db + backend + frontend (nginx) together
- **Auth:** email + password (bcrypt), JWT bearer tokens

## Run with Docker (recommended)

Needs Docker with Compose. One command starts PostgreSQL, the API and the web app.

```bash
cp .env.example .env      # set SECRET_KEY and POSTGRES_PASSWORD (see the comments inside)
docker compose up --build
```

- App: http://localhost:8080 (nginx serves the React build and proxies `/api` to the backend)
- API docs: http://localhost:8080/docs
- The backend applies Alembic migrations on every start.
- Demo data (`demo@example.com` / `demo12345`): `docker compose exec backend python seed.py`
  (add `--reset` to recreate it).
- Database shell: `docker compose exec db psql -U internship`
- Stop: `docker compose down`. Add `-v` to also delete the database volume.

Postgres is published on `127.0.0.1:5432` only, so you can use `psql` or run the tests
against it (see Tests). Change ports with `APP_PORT` and `POSTGRES_PORT` in `.env`.

## Run locally without Docker

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # then set SECRET_KEY (see the comment inside)
alembic upgrade head          # create / update the schema
python seed.py                # optional: demo@example.com / demo12345 with sample data
uvicorn main:app --reload --port 8000
```

API docs are served at http://localhost:8000/docs.

A database created before Alembic was added already has the first three tables.
Mark it as up to date with the first migration, then upgrade:
`alembic stamp 0001 && alembic upgrade head`.

### Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173, /api is proxied to port 8000
```

## Tests

```bash
cd backend
pytest
```

By default the tests use a temporary SQLite file. To run the same tests on PostgreSQL,
start the `db` service, create a dedicated database (its tables are dropped and recreated,
so the name must contain `test`) and pass its URL:

```bash
docker compose up -d db
docker compose exec db psql -U internship -c "CREATE DATABASE internship_test"
TEST_DATABASE_URL=postgresql://internship:<POSTGRES_PASSWORD>@localhost:5432/internship_test pytest
```

Covers registration and login, validation, per-user data isolation, status history,
UTC timestamps, search and filters, the dashboard numbers, Alembic migrations and the
demo seed. Tests are grouped by user story: `test_auth.py` (US-01/02),
`test_applications.py` (US-03..07, US-09), `test_dashboard.py` (US-08/10),
`test_infrastructure.py` (migrations, seed, CORS).

Frontend helpers (CSV export, date handling) have plain Node tests, no extra packages:

```bash
cd frontend
npm test
```

For Postman, import `backend/docs/openapi.json`, or point Postman at
http://localhost:8000/openapi.json. Regenerate the file after changing the API:

```bash
python -c "import json; from main import app; json.dump(app.openapi(), open('docs/openapi.json','w'), indent=2)"
```

## Configuration

| Variable | Where | Purpose |
|---|---|---|
| `SECRET_KEY` | backend | Signs JWTs. Required, no default. |
| `DATABASE_URL` | backend | `sqlite:///./internship_tracker.db` (default) or a `postgresql://` URL (set automatically by Docker Compose). |
| `CORS_ORIGINS` | backend | Comma-separated frontend origins allowed to call the API. |

## Status pipeline

`Saved` to `Applied` to `Interview` to `Offer` or `Rejected`. Any status can be set from
the application drawer or by dragging a card between columns. Every change is stored in
`status_history` with its timestamp.

Response rate on the overview is the share of submitted applications (anything past
Saved) that reached Interview or Offer at any point.
