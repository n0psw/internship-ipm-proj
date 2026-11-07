# Internship Tracker

One place for every internship application: a Kanban board, deadlines, follow-ups,
interview dates, contacts, notes and status history.

- **Frontend:** React 18 + Vite (`frontend/`)
- **Backend:** FastAPI + SQLAlchemy + Alembic (`backend/`)
- **Database:** SQLite by default (set `DATABASE_URL` to use PostgreSQL)
- **Auth:** email + password (bcrypt), JWT bearer tokens

## Run locally

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

Covers registration and login, validation, per-user data isolation, status history,
UTC timestamps, search and filters, and the dashboard numbers.

For Postman, import `backend/docs/openapi.json`, or point Postman at
http://localhost:8000/openapi.json. Regenerate the file after changing the API:

```bash
python -c "import json; from main import app; json.dump(app.openapi(), open('docs/openapi.json','w'), indent=2)"
```

## Configuration

| Variable | Where | Purpose |
|---|---|---|
| `SECRET_KEY` | backend | Signs JWTs. Required, no default. |
| `DATABASE_URL` | backend | `sqlite:///./internship_tracker.db` (default) or a `postgresql://` URL. |
| `CORS_ORIGINS` | backend | Comma-separated frontend origins allowed to call the API. |

## Status pipeline

`Saved` to `Applied` to `Interview` to `Offer` or `Rejected`. Any status can be set from
the application drawer or by dragging a card between columns. Every change is stored in
`status_history` with its timestamp.

Response rate on the overview is the share of submitted applications (anything past
Saved) that reached Interview or Offer at any point.
