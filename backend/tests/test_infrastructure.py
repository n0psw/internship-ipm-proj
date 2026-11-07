"""Health endpoint, CORS, Alembic migrations and the demo seed script."""
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

import models
import seed
from database import Base, SessionLocal

BACKEND = Path(__file__).resolve().parent.parent


def test_health_and_root_are_public(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 200


def test_cors_allows_the_local_frontend_only(client):
    ok = client.options(
        "/api/applications",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = client.options(
        "/api/applications",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in bad.headers


def test_openapi_json_in_repo_is_up_to_date(client):
    import json

    committed = json.loads((BACKEND / "docs" / "openapi.json").read_text())
    assert committed == client.get("/openapi.json").json(), (
        "backend/docs/openapi.json is stale; regenerate it (see README)"
    )


def test_alembic_upgrade_head_matches_the_models(tmp_path):
    db_file = tmp_path / "migrated.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_file}"}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

    insp = inspect(create_engine(f"sqlite:///{db_file}"))
    for table in Base.metadata.sorted_tables:
        assert insp.has_table(table.name), f"missing table {table.name}"
        migrated = {c["name"] for c in insp.get_columns(table.name)}
        assert migrated == {c.name for c in table.columns}, f"column mismatch in {table.name}"


def test_demo_seed_creates_loginable_user_and_is_idempotent(client, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["seed.py"])
    seed.main()
    login = client.post("/api/auth/login", json={"email": seed.DEMO_EMAIL, "password": seed.DEMO_PASSWORD})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    first = client.get("/api/applications", headers=headers).json()
    assert len(first) == 8

    seed.main()  # second run must not duplicate anything
    assert len(client.get("/api/applications", headers=headers).json()) == 8


def test_demo_seed_reset_recreates_data(client, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["seed.py"])
    seed.main()
    monkeypatch.setattr(sys, "argv", ["seed.py", "--reset"])
    seed.main()
    db = SessionLocal()
    try:
        assert db.query(models.User).count() == 1
        assert db.query(models.Application).count() == 8
        # every seeded application has a history row for each status it passed through
        assert db.query(models.StatusHistory).count() >= 8
    finally:
        db.close()


def test_demo_seed_data_is_internally_consistent(client, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["seed.py"])
    seed.main()
    token = client.post("/api/auth/login", json={"email": seed.DEMO_EMAIL, "password": seed.DEMO_PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    for app in client.get("/api/applications", headers=headers).json():
        last = client.get(f"/api/applications/{app['id']}/history", headers=headers).json()[0]
        assert last["new_status"] == app["status"], app["company"]
