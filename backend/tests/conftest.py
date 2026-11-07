import os
import sys
import tempfile
from pathlib import Path

# Must be set before the app modules are imported.
# SQLite in a temp file by default. To run the same tests on PostgreSQL:
#   TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/internship_test pytest
# (the tables of that database are dropped and recreated, use a dedicated one).
_db = Path(tempfile.mkdtemp()) / "test.db"
_url = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{_db}"
if not _url.startswith("sqlite") and "test" not in _url.rsplit("/", 1)[-1]:
    raise RuntimeError("TEST_DATABASE_URL must point to a database whose name contains 'test': tests drop all tables.")
os.environ["DATABASE_URL"] = _url
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from database import Base, engine  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _register(client, email, name="Test User", password="password123"):
    r = client.post("/api/auth/register", json={"name": name, "email": email, "password": password})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def auth_headers(client):
    return _register(client, "alice@example.com")


@pytest.fixture
def other_headers(client):
    return _register(client, "bob@example.com", name="Bob")


@pytest.fixture
def make_app(client, auth_headers):
    def _make(headers=None, **fields):
        payload = {"company": "Acme", "position": "Intern", **fields}
        r = client.post("/api/applications", json=payload, headers=headers or auth_headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _make
