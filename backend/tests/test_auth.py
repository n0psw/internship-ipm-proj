"""US-01 / US-02: registration, login, tokens and per-user privacy."""
from datetime import timedelta

import pytest

import auth
from database import SessionLocal
import models


def register(client, **overrides):
    payload = {"name": "Aruzhan", "email": "aruzhan@mail.kz", "password": "intern2026", **overrides}
    return client.post("/api/auth/register", json=payload)


def test_register_returns_token_and_user_without_password(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["token_type"] == "bearer" and body["access_token"]
    assert body["user"]["name"] == "Aruzhan"
    assert "password" not in body["user"] and "password_hash" not in body["user"]


def test_new_user_starts_with_empty_dashboard(client):
    token = register(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    stats = client.get("/api/dashboard/stats", headers=headers).json()
    assert stats["total"] == 0 and stats["upcoming"] == []
    assert client.get("/api/applications", headers=headers).json() == []


def test_password_is_stored_hashed(client):
    register(client)
    db = SessionLocal()
    try:
        user = db.query(models.User).one()
        assert user.password_hash != "intern2026"
        assert auth.verify_password("intern2026", user.password_hash)
    finally:
        db.close()


def test_duplicate_email_is_rejected_and_no_second_account_created(client):
    register(client)
    r = register(client, email="ARUZHAN@mail.kz")
    assert r.status_code == 400
    assert r.json()["detail"] == "Email already registered"
    db = SessionLocal()
    try:
        assert db.query(models.User).count() == 1
    finally:
        db.close()


@pytest.mark.parametrize("field", ["name", "email", "password"])
def test_register_requires_every_field(client, field):
    payload = {"name": "A", "email": "a@example.com", "password": "password123"}
    payload.pop(field)
    assert client.post("/api/auth/register", json=payload).status_code == 422


def test_password_length_boundaries(client):
    assert register(client, email="a7@mail.kz", password="1234567").status_code == 422
    assert register(client, email="a8@mail.kz", password="12345678").status_code == 201
    assert register(client, email="a72@mail.kz", password="x" * 72).status_code == 201
    assert register(client, email="a73@mail.kz", password="x" * 73).status_code == 422


def test_unicode_name_roundtrip(client):
    r = register(client, name="Қанат Әлиев")
    assert r.json()["user"]["name"] == "Қанат Әлиев"


def test_login_is_case_insensitive_and_trims_email(client):
    register(client)
    r = client.post("/api/auth/login", json={"email": "  Aruzhan@Mail.kz ", "password": "intern2026"})
    assert r.status_code == 200


def test_login_error_does_not_reveal_which_emails_exist(client):
    register(client)
    wrong_password = client.post("/api/auth/login", json={"email": "aruzhan@mail.kz", "password": "nope-nope"})
    unknown_user = client.post("/api/auth/login", json={"email": "nobody@mail.kz", "password": "intern2026"})
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json() == {"detail": "Invalid email or password"}


def test_me_returns_current_user(client):
    token = register(client).json()["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200 and r.json()["email"] == "aruzhan@mail.kz"


def test_expired_token_gets_401(client):
    register(client)
    expired = auth.create_access_token({"sub": "1"}, expires_delta=timedelta(minutes=-1))
    for url in ("/api/auth/me", "/api/applications", "/api/dashboard/stats"):
        assert client.get(url, headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_token_for_deleted_user_gets_401(client):
    token = register(client).json()["access_token"]
    db = SessionLocal()
    try:
        db.delete(db.query(models.User).one())
        db.commit()
    finally:
        db.close()
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_signed_with_other_key_gets_401(client):
    import jwt

    forged = jwt.encode({"sub": "1"}, "some-other-secret-key-123456789012345", algorithm="HS256")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


@pytest.mark.parametrize(
    "method,url",
    [
        ("get", "/api/applications"),
        ("post", "/api/applications"),
        ("get", "/api/applications/1"),
        ("patch", "/api/applications/1"),
        ("delete", "/api/applications/1"),
        ("get", "/api/applications/1/history"),
        ("get", "/api/dashboard/stats"),
        ("get", "/api/auth/me"),
    ],
)
def test_every_protected_endpoint_returns_401_without_token(client, method, url):
    r = getattr(client, method)(url)
    assert r.status_code == 401
    assert "company" not in r.text


def test_new_user_sees_nothing_of_other_users(client, auth_headers, make_app):
    make_app(company="Secret Co")
    c = {"Authorization": "Bearer " + register(client, email="c@mail.kz").json()["access_token"]}
    assert client.get("/api/applications", headers=c).json() == []
    assert client.get("/api/applications", params={"search": "Secret"}, headers=c).json() == []
    stats = client.get("/api/dashboard/stats", headers=c).json()
    assert stats["total"] == 0 and stats["by_status"]["Saved"] == 0


def test_status_change_and_delete_of_foreign_application_leave_it_untouched(
    client, auth_headers, other_headers, make_app
):
    app = make_app()
    url = f"/api/applications/{app['id']}"
    client.patch(url, json={"status": "Applied"}, headers=auth_headers)

    assert client.patch(url, json={"status": "Rejected", "company": "Hacked"}, headers=other_headers).status_code == 404
    assert client.delete(url, headers=other_headers).status_code == 404

    mine = client.get(url, headers=auth_headers).json()
    assert mine["status"] == "Applied" and mine["company"] == "Acme"
    assert len(client.get(url + "/history", headers=auth_headers).json()) == 2


def test_dashboard_counts_are_per_user(client, auth_headers, other_headers, make_app):
    make_app(company="A1")
    make_app(company="A2")
    make_app(headers=other_headers, company="B1", status="Applied")
    mine = client.get("/api/dashboard/stats", headers=auth_headers).json()
    theirs = client.get("/api/dashboard/stats", headers=other_headers).json()
    assert (mine["total"], mine["submitted"]) == (2, 0)
    assert (theirs["total"], theirs["submitted"]) == (1, 1)
