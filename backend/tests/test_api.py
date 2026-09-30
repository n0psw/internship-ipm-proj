from datetime import date, datetime, timedelta, timezone

import pytest


# ─── Auth ─────────────────────────────────────────────────────────────────────

def test_register_and_login(client):
    r = client.post("/api/auth/register", json={"name": "A", "email": "A@Example.com", "password": "password123"})
    assert r.status_code == 201
    assert r.json()["user"]["email"] == "a@example.com"  # stored lowercase

    r = client.post("/api/auth/login", json={"email": "a@EXAMPLE.com", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["access_token"]


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "A", "email": "not-an-email", "password": "password123"},
        {"name": "  ", "email": "a@example.com", "password": "password123"},
        {"name": "A", "email": "a@example.com", "password": "short"},
        {"name": "A", "email": "a@example.com", "password": "x" * 100},
    ],
)
def test_register_rejects_invalid_input(client, payload):
    assert client.post("/api/auth/register", json=payload).status_code == 422


def test_register_duplicate_email_case_insensitive(client, auth_headers):
    r = client.post("/api/auth/register", json={"name": "X", "email": "ALICE@example.com", "password": "password123"})
    assert r.status_code == 400


def test_login_wrong_password(client, auth_headers):
    r = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "wrong-password"})
    assert r.status_code == 401


def test_protected_routes_require_token(client):
    assert client.get("/api/applications").status_code == 401
    assert client.get("/api/dashboard/stats").status_code == 401
    assert client.get("/api/applications", headers={"Authorization": "Bearer garbage"}).status_code == 401


# ─── Validation ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "payload",
    [
        {"company": "", "position": "Intern"},
        {"company": "Acme", "position": "   "},
        {"company": "Acme", "position": "Intern", "status": "Hired"},
        {"company": "Acme", "position": "Intern", "job_url": "javascript:alert(1)"},
        {"company": "Acme", "position": "Intern", "deadline": "not-a-date"},
        {"company": "A" * 201, "position": "Intern"},
    ],
)
def test_create_rejects_invalid_input(client, auth_headers, payload):
    assert client.post("/api/applications", json=payload, headers=auth_headers).status_code == 422


def test_create_normalises_input(client, auth_headers):
    r = client.post(
        "/api/applications",
        json={"company": "  Acme  ", "position": "Intern", "job_url": "acme.com/jobs", "location": "  "},
        headers=auth_headers,
    )
    body = r.json()
    assert body["company"] == "Acme"
    assert body["job_url"] == "https://acme.com/jobs"
    assert body["location"] is None
    assert body["status"] == "Saved"


@pytest.mark.parametrize("payload", [{"status": None}, {"company": None}, {"position": ""}])
def test_patch_rejects_null_or_blank_required_fields(client, auth_headers, make_app, payload):
    app = make_app()
    r = client.patch(f"/api/applications/{app['id']}", json=payload, headers=auth_headers)
    assert r.status_code == 422  # used to be a 500


def test_patch_can_clear_optional_fields(client, auth_headers, make_app):
    app = make_app(deadline="2026-10-15", notes="hello")
    r = client.patch(f"/api/applications/{app['id']}", json={"deadline": None, "notes": None}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["deadline"] is None and r.json()["notes"] is None


# ─── Ownership ────────────────────────────────────────────────────────────────

def test_users_cannot_see_or_touch_each_others_data(client, auth_headers, other_headers, make_app):
    app = make_app()
    url = f"/api/applications/{app['id']}"

    assert client.get(url, headers=other_headers).status_code == 404
    assert client.patch(url, json={"status": "Offer"}, headers=other_headers).status_code == 404
    assert client.get(url + "/history", headers=other_headers).status_code == 404
    assert client.delete(url, headers=other_headers).status_code == 404
    assert client.get("/api/applications", headers=other_headers).json() == []
    assert client.get(url, headers=auth_headers).json()["status"] == "Saved"


# ─── Status history ───────────────────────────────────────────────────────────

def test_status_history_records_changes_only(client, auth_headers, make_app):
    app = make_app()
    url = f"/api/applications/{app['id']}"
    client.patch(url, json={"status": "Applied"}, headers=auth_headers)
    client.patch(url, json={"status": "Applied", "notes": "same status again"}, headers=auth_headers)
    client.patch(url, json={"status": "Interview"}, headers=auth_headers)

    history = client.get(url + "/history", headers=auth_headers).json()
    assert [(h["old_status"], h["new_status"]) for h in history] == [
        ("Applied", "Interview"),
        ("Saved", "Applied"),
        (None, "Saved"),
    ]


def test_delete_removes_application_and_history(client, auth_headers, make_app):
    app = make_app()
    assert client.delete(f"/api/applications/{app['id']}", headers=auth_headers).status_code == 200
    assert client.get(f"/api/applications/{app['id']}", headers=auth_headers).status_code == 404


# ─── Timestamps ───────────────────────────────────────────────────────────────

def test_datetimes_are_utc_with_z_suffix(client, auth_headers, make_app):
    app = make_app(interview_date="2026-10-05T14:00:00+05:00")
    assert app["interview_date"] == "2026-10-05T09:00:00Z"
    assert app["created_at"].endswith("Z") and app["updated_at"].endswith("Z")

    fetched = client.get(f"/api/applications/{app['id']}", headers=auth_headers).json()
    assert fetched["interview_date"] == "2026-10-05T09:00:00Z"


# ─── Search and filters ───────────────────────────────────────────────────────

def test_search_and_filters(client, auth_headers, make_app):
    make_app(company="Google", position="SWE Intern", location="Zurich", status="Applied", deadline="2026-10-01")
    make_app(company="Yandex", position="Analyst", location="Remote", deadline="2026-11-01")
    make_app(company="100% Remote Co", position="Intern", location="Almaty")

    def ids(**params):
        r = client.get("/api/applications", params=params, headers=auth_headers)
        assert r.status_code == 200, r.text
        return sorted(a["company"] for a in r.json())

    assert ids(search="goo") == ["Google"]
    assert ids(search="analyst") == ["Yandex"]
    assert ids(search="%") == ["100% Remote Co"]  # wildcard matched literally
    assert ids(search="_") == []
    assert ids(location="remote") == ["Yandex"]
    assert ids(status="Applied") == ["Google"]
    assert ids(deadline_from="2026-10-15") == ["Yandex"]
    assert ids(deadline_to="2026-10-15") == ["Google"]
    assert ids(deadline_from="2026-10-01", deadline_to="2026-11-01") == ["Google", "Yandex"]
    assert client.get("/api/applications", params={"status": "Bogus"}, headers=auth_headers).status_code == 422
    assert client.get("/api/applications", params={"sort": "deadline"}, headers=auth_headers).status_code == 200


def test_sort_by_deadline_puts_missing_last(client, auth_headers, make_app):
    make_app(company="NoDate")
    make_app(company="Late", deadline="2026-12-01")
    make_app(company="Soon", deadline="2026-10-01")
    r = client.get("/api/applications", params={"sort": "deadline"}, headers=auth_headers)
    assert [a["company"] for a in r.json()] == ["Soon", "Late", "NoDate"]


# ─── Dashboard ────────────────────────────────────────────────────────────────

def test_dashboard_counts_and_response_rate(client, auth_headers, make_app):
    def move(app, *statuses):
        for s in statuses:
            client.patch(f"/api/applications/{app['id']}", json={"status": s}, headers=auth_headers)

    make_app(company="OnlySaved")
    move(make_app(company="Silent"), "Applied")
    move(make_app(company="Talked"), "Applied", "Interview")
    move(make_app(company="Won"), "Applied", "Interview", "Offer")
    move(make_app(company="Ghosted"), "Applied", "Rejected")

    stats = client.get("/api/dashboard/stats", headers=auth_headers).json()
    assert stats["total"] == 5
    assert stats["by_status"] == {"Saved": 1, "Applied": 1, "Interview": 1, "Offer": 1, "Rejected": 1}
    assert stats["submitted"] == 4
    assert stats["response_rate"] == 50  # Talked + Won out of 4 submitted


def test_dashboard_response_rate_is_none_before_any_submission(client, auth_headers, make_app):
    make_app()
    assert client.get("/api/dashboard/stats", headers=auth_headers).json()["response_rate"] is None


def test_dashboard_upcoming_uses_client_date(client, auth_headers, make_app):
    today = date(2026, 10, 1)
    make_app(company="Overdue", deadline=(today - timedelta(days=2)).isoformat())
    make_app(company="Tomorrow", deadline=(today + timedelta(days=1)).isoformat())
    make_app(company="TooFar", deadline=(today + timedelta(days=30)).isoformat())
    make_app(company="Closed", deadline=(today + timedelta(days=1)).isoformat(), status="Rejected")
    make_app(company="Chase", follow_up_date=today.isoformat(), status="Applied")

    stats = client.get("/api/dashboard/stats", params={"today": today.isoformat()}, headers=auth_headers).json()
    got = [(i["company"], i["kind"], i["overdue"]) for i in stats["upcoming"]]
    assert got == [
        ("Overdue", "deadline", True),
        ("Chase", "follow_up", False),
        ("Tomorrow", "deadline", False),
    ]


def test_dashboard_upcoming_includes_interviews_in_window(client, auth_headers, make_app):
    soon = (datetime.now(timezone.utc) + timedelta(days=2)).replace(microsecond=0)
    past = datetime.now(timezone.utc) - timedelta(days=2)
    make_app(company="Soon", interview_date=soon.isoformat())
    make_app(company="Past", interview_date=past.isoformat())

    upcoming = client.get("/api/dashboard/stats", headers=auth_headers).json()["upcoming"]
    assert [(i["company"], i["kind"]) for i in upcoming] == [("Soon", "interview")]
    assert upcoming[0]["when"].endswith("Z")
