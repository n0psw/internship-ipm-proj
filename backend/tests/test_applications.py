"""US-03 .. US-07 and US-09: the application form, status moves, dates, history, search."""
from datetime import date, timedelta

import pytest

from database import SessionLocal
import models

STATUSES = ["Saved", "Applied", "Interview", "Offer", "Rejected"]


def url(app):
    return f"/api/applications/{app['id']}"


def history(client, headers, app):
    return [(h["old_status"], h["new_status"]) for h in client.get(url(app) + "/history", headers=headers).json()]


# ─── US-03 add ────────────────────────────────────────────────────────────────

def test_create_with_company_position_and_link_lands_in_saved(client, auth_headers):
    r = client.post(
        "/api/applications",
        json={"company": "Kaspi", "position": "Backend Intern", "job_url": "https://kaspi.kz/careers"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "Saved" and body["job_url"] == "https://kaspi.kz/careers"
    assert len(client.get("/api/applications", headers=auth_headers).json()) == 1


@pytest.mark.parametrize("empty", [None, "", "   "])
def test_link_is_optional(client, auth_headers, empty):
    r = client.post("/api/applications", json={"company": "Kaspi", "position": "Intern", "job_url": empty}, headers=auth_headers)
    assert r.status_code == 201 and r.json()["job_url"] is None


@pytest.mark.parametrize("field", ["company", "position"])
@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_required_fields_reject_blank_values_and_save_nothing(client, auth_headers, field, value):
    payload = {"company": "Kaspi", "position": "Intern", field: value}
    assert client.post("/api/applications", json=payload, headers=auth_headers).status_code == 422
    assert client.get("/api/applications", headers=auth_headers).json() == []


@pytest.mark.parametrize("field", ["company", "position"])
def test_required_fields_cannot_be_missing(client, auth_headers, field):
    payload = {"company": "Kaspi", "position": "Intern"}
    payload.pop(field)
    assert client.post("/api/applications", json=payload, headers=auth_headers).status_code == 422


@pytest.mark.parametrize(
    "link",
    ["kaspi careers", "http://", "ftp://example.com/file", "javascript:alert(1)", "mailto:hr@kaspi.kz", "https://exa mple.com"],
)
def test_invalid_links_are_rejected(client, auth_headers, link):
    r = client.post("/api/applications", json={"company": "Kaspi", "position": "Intern", "job_url": link}, headers=auth_headers)
    assert r.status_code == 422
    assert client.get("/api/applications", headers=auth_headers).json() == []


@pytest.mark.parametrize(
    "link,expected",
    [
        ("kaspi.kz/careers", "https://kaspi.kz/careers"),
        ("http://example.com", "http://example.com"),
        ("localhost:3000/jobs", "https://localhost:3000/jobs"),
        ("  https://example.com/a?b=1&c=2  ", "https://example.com/a?b=1&c=2"),
    ],
)
def test_valid_links_are_accepted(client, auth_headers, link, expected):
    r = client.post("/api/applications", json={"company": "X", "position": "Y", "job_url": link}, headers=auth_headers)
    assert r.status_code == 201 and r.json()["job_url"] == expected


def test_kazakh_and_russian_text_is_stored_as_typed(client, auth_headers):
    r = client.post("/api/applications", json={"company": "Қазақтелеком", "position": "Стажёр-аналитик", "notes": "Сәлем! 你好"}, headers=auth_headers)
    app = r.json()
    fetched = client.get(url(app), headers=auth_headers).json()
    assert (fetched["company"], fetched["position"], fetched["notes"]) == ("Қазақтелеком", "Стажёр-аналитик", "Сәлем! 你好")


def test_field_length_limits(client, auth_headers):
    base = {"company": "A", "position": "B"}
    assert client.post("/api/applications", json={**base, "company": "A" * 200}, headers=auth_headers).status_code == 201
    assert client.post("/api/applications", json={**base, "position": "B" * 201}, headers=auth_headers).status_code == 422
    assert client.post("/api/applications", json={**base, "notes": "n" * 10001}, headers=auth_headers).status_code == 422


def test_create_with_explicit_status_records_it_as_first_history_entry(client, auth_headers, make_app):
    app = make_app(status="Applied")
    assert history(client, auth_headers, app) == [(None, "Applied")]


def test_client_cannot_set_owner_or_id_on_create(client, auth_headers, other_headers, make_app):
    r = client.post("/api/applications", json={"company": "A", "position": "B", "user_id": 999, "id": 12345}, headers=auth_headers)
    body = r.json()
    assert body["user_id"] != 999 and body["id"] != 12345
    assert client.get("/api/applications", headers=other_headers).json() == []


def test_unknown_application_id_returns_404(client, auth_headers):
    assert client.get("/api/applications/99999", headers=auth_headers).status_code == 404
    assert client.patch("/api/applications/99999", json={"notes": "x"}, headers=auth_headers).status_code == 404
    assert client.delete("/api/applications/99999", headers=auth_headers).status_code == 404


# ─── US-04 edit / delete ──────────────────────────────────────────────────────

def test_edit_location_persists(client, auth_headers, make_app):
    app = make_app(location="Almaty")
    client.patch(url(app), json={"location": "Astana"}, headers=auth_headers)
    assert client.get(url(app), headers=auth_headers).json()["location"] == "Astana"


def test_patch_changes_only_the_sent_fields(client, auth_headers, make_app):
    app = make_app(location="Almaty", notes="keep me", deadline="2026-12-01")
    r = client.patch(url(app), json={"company": "NewCo"}, headers=auth_headers).json()
    assert (r["company"], r["location"], r["notes"], r["deadline"]) == ("NewCo", "Almaty", "keep me", "2026-12-01")


def test_failed_edit_keeps_old_values(client, auth_headers, make_app):
    app = make_app(company="Acme", location="Almaty")
    assert client.patch(url(app), json={"company": "", "location": "Astana"}, headers=auth_headers).status_code == 422
    fetched = client.get(url(app), headers=auth_headers).json()
    assert (fetched["company"], fetched["location"]) == ("Acme", "Almaty")


def test_edit_updates_updated_at_but_not_created_at(client, auth_headers, make_app):
    app = make_app()
    changed = client.patch(url(app), json={"notes": "n"}, headers=auth_headers).json()
    assert changed["created_at"] == app["created_at"]
    assert changed["updated_at"] >= app["updated_at"]


def test_delete_removes_history_rows_from_database(client, auth_headers, make_app):
    app = make_app()
    client.patch(url(app), json={"status": "Applied"}, headers=auth_headers)
    assert client.delete(url(app), headers=auth_headers).status_code == 200
    db = SessionLocal()
    try:
        assert db.query(models.StatusHistory).count() == 0
        assert db.query(models.Application).count() == 0
    finally:
        db.close()


def test_deleted_application_is_gone_everywhere_and_cannot_be_edited(client, auth_headers, make_app):
    app = make_app()
    client.delete(url(app), headers=auth_headers)
    assert client.get("/api/applications", headers=auth_headers).json() == []
    assert client.get(url(app) + "/history", headers=auth_headers).status_code == 404
    assert client.patch(url(app), json={"status": "Applied"}, headers=auth_headers).status_code == 404
    assert client.delete(url(app), headers=auth_headers).status_code == 404


# ─── US-05 / US-07 status moves and history ───────────────────────────────────

@pytest.mark.parametrize("old", STATUSES)
@pytest.mark.parametrize("new", STATUSES)
def test_any_status_can_move_to_any_other(client, auth_headers, make_app, old, new):
    app = make_app(status=old)
    r = client.patch(url(app), json={"status": new}, headers=auth_headers)
    assert r.status_code == 200 and r.json()["status"] == new
    expected = [(None, old)] if old == new else [(old, new), (None, old)]
    assert history(client, auth_headers, app) == expected


def test_invalid_status_is_rejected_and_not_recorded(client, auth_headers, make_app):
    app = make_app()
    assert client.patch(url(app), json={"status": "Hired"}, headers=auth_headers).status_code == 422
    assert client.get(url(app), headers=auth_headers).json()["status"] == "Saved"
    assert history(client, auth_headers, app) == [(None, "Saved")]


def test_move_persists_after_reload(client, auth_headers, make_app):
    app = make_app()
    client.patch(url(app), json={"status": "Applied"}, headers=auth_headers)
    listed = client.get("/api/applications", headers=auth_headers).json()
    assert [a["status"] for a in listed] == ["Applied"]


def test_new_application_has_exactly_one_history_entry_with_timestamp(client, auth_headers, make_app):
    app = make_app()
    entries = client.get(url(app) + "/history", headers=auth_headers).json()
    assert len(entries) == 1
    assert entries[0]["old_status"] is None and entries[0]["new_status"] == "Saved"
    assert entries[0]["changed_at"].endswith("Z")


def test_history_is_newest_first_with_three_entries(client, auth_headers, make_app):
    app = make_app()
    for s in ("Applied", "Interview"):
        client.patch(url(app), json={"status": s}, headers=auth_headers)
    assert history(client, auth_headers, app) == [("Applied", "Interview"), ("Saved", "Applied"), (None, "Saved")]


def test_moving_backwards_adds_an_entry(client, auth_headers, make_app):
    app = make_app()
    for s in ("Applied", "Interview", "Applied"):
        client.patch(url(app), json={"status": s}, headers=auth_headers)
    assert history(client, auth_headers, app)[0] == ("Interview", "Applied")


def test_editing_other_fields_adds_no_history_entry(client, auth_headers, make_app):
    app = make_app()
    client.patch(url(app), json={"location": "Almaty", "notes": "x"}, headers=auth_headers)
    assert history(client, auth_headers, app) == [(None, "Saved")]


def test_history_of_one_application_does_not_leak_into_another(client, auth_headers, make_app):
    a, b = make_app(company="A"), make_app(company="B")
    client.patch(url(a), json={"status": "Applied"}, headers=auth_headers)
    assert history(client, auth_headers, b) == [(None, "Saved")]


# ─── US-06 dates ──────────────────────────────────────────────────────────────

def test_dates_roundtrip_and_can_be_cleared(client, auth_headers, make_app):
    app = make_app(deadline="2026-10-22", follow_up_date="2026-10-25", interview_date="2026-10-22T15:00:00Z")
    assert (app["deadline"], app["follow_up_date"], app["interview_date"]) == ("2026-10-22", "2026-10-25", "2026-10-22T15:00:00Z")
    cleared = client.patch(url(app), json={"deadline": None, "follow_up_date": None, "interview_date": None}, headers=auth_headers).json()
    assert cleared["deadline"] is None and cleared["follow_up_date"] is None and cleared["interview_date"] is None


def test_application_without_dates_returns_nulls(client, auth_headers, make_app):
    app = make_app()
    assert app["deadline"] is None and app["follow_up_date"] is None and app["interview_date"] is None


@pytest.mark.parametrize("field,value", [("deadline", "2026-13-40"), ("deadline", "tomorrow"), ("follow_up_date", "31/12/2026"), ("interview_date", "soon")])
def test_invalid_dates_are_rejected(client, auth_headers, field, value):
    r = client.post("/api/applications", json={"company": "A", "position": "B", field: value}, headers=auth_headers)
    assert r.status_code == 422


def test_interview_time_is_stored_as_utc_whatever_offset_is_sent(client, auth_headers, make_app):
    app = make_app(interview_date="2026-10-22T15:00:00+05:00")
    assert app["interview_date"] == "2026-10-22T10:00:00Z"
    app2 = make_app(interview_date="2026-10-22T15:00:00")  # no offset: treated as UTC
    assert app2["interview_date"] == "2026-10-22T15:00:00Z"


# ─── US-09 search and filters ─────────────────────────────────────────────────

@pytest.fixture
def twenty(client, auth_headers, make_app):
    for i in range(20):
        make_app(company=f"Company {i:02d}", position="Intern", location="Almaty" if i % 2 else "Astana")
    return 20


def listing(client, headers, **params):
    r = client.get("/api/applications", params=params, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_search_matches_company_or_position_case_insensitively(client, auth_headers, make_app):
    make_app(company="Kaspi", position="Backend Intern")
    make_app(company="Other", position="Kaspian Analyst")
    make_app(company="Nope", position="Intern")
    assert {a["company"] for a in listing(client, auth_headers, search="kas")} == {"Kaspi", "Other"}
    assert {a["company"] for a in listing(client, auth_headers, search="KASPI")} == {"Kaspi", "Other"}


def test_search_combined_with_status(client, auth_headers, make_app):
    make_app(company="Kaspi", status="Interview")
    make_app(company="Kaspi Bank", status="Saved")
    got = listing(client, auth_headers, search="Kaspi", status="Interview")
    assert [a["company"] for a in got] == ["Kaspi"]


def test_status_filter_alone(client, auth_headers, make_app):
    make_app(company="A", status="Rejected")
    make_app(company="B")
    assert [a["company"] for a in listing(client, auth_headers, status="Rejected")] == ["A"]


def test_whitespace_only_search_acts_like_no_search(client, auth_headers, twenty):
    assert len(listing(client, auth_headers, search="   ")) == 20
    assert len(listing(client, auth_headers, search="")) == 20


def test_search_with_no_match_returns_empty_list(client, auth_headers, twenty):
    assert listing(client, auth_headers, search="Google") == []


def test_search_is_trimmed(client, auth_headers, make_app):
    make_app(company="Kaspi")
    assert len(listing(client, auth_headers, search="  kaspi ")) == 1


def test_search_matches_cyrillic_and_kazakh_text(client, auth_headers, make_app):
    make_app(company="Қазақтелеком", position="Стажёр-аналитик")
    assert len(listing(client, auth_headers, search="Қазақ")) == 1
    assert len(listing(client, auth_headers, search="аналитик")) == 1


def test_search_does_not_cross_users(client, auth_headers, other_headers, make_app):
    make_app(headers=other_headers, company="Kaspi")
    assert listing(client, auth_headers, search="Kaspi") == []


def test_search_treats_sql_wildcards_and_quotes_literally(client, auth_headers, make_app):
    make_app(company="O'Reilly")
    make_app(company="Plain")
    assert [a["company"] for a in listing(client, auth_headers, search="O'Re")] == ["O'Reilly"]
    assert listing(client, auth_headers, search="'; DROP TABLE applications; --") == []
    assert len(listing(client, auth_headers)) == 2


def test_sort_by_company(client, auth_headers, make_app):
    for name in ("Charlie", "Alpha", "Bravo"):
        make_app(company=name)
    assert [a["company"] for a in listing(client, auth_headers, sort="company")] == ["Alpha", "Bravo", "Charlie"]


def test_default_order_is_newest_first(client, auth_headers, make_app):
    for name in ("First", "Second", "Third"):
        make_app(company=name)
    assert [a["company"] for a in listing(client, auth_headers)] == ["Third", "Second", "First"]


def test_invalid_sort_is_rejected(client, auth_headers):
    assert client.get("/api/applications", params={"sort": "salary"}, headers=auth_headers).status_code == 422


def test_deadline_range_is_inclusive_and_skips_missing_deadlines(client, auth_headers, make_app):
    make_app(company="NoDate")
    make_app(company="On", deadline="2026-10-15")
    make_app(company="Before", deadline="2026-10-14")
    got = listing(client, auth_headers, deadline_from="2026-10-15", deadline_to="2026-10-15")
    assert [a["company"] for a in got] == ["On"]


def test_listing_returns_all_20(client, auth_headers, twenty):
    assert len(listing(client, auth_headers)) == 20
    assert len(listing(client, auth_headers, location="almaty")) == 10
