"""US-08 overview counts and US-10 'next 7 days' list."""
from datetime import date, datetime, timedelta, timezone

TODAY = date(2026, 10, 14)


def day(n):
    return (TODAY + timedelta(days=n)).isoformat()


def stats(client, headers, **params):
    r = client.get("/api/dashboard/stats", params={"today": TODAY.isoformat(), **params}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def upcoming(client, headers):
    return [(i["company"], i["kind"], i["overdue"]) for i in stats(client, headers)["upcoming"]]


# ─── US-08 counts ─────────────────────────────────────────────────────────────

def test_empty_account_shows_zeros_for_every_status(client, auth_headers):
    s = stats(client, auth_headers)
    assert s["total"] == 0 and s["submitted"] == 0 and s["response_rate"] is None and s["upcoming"] == []
    assert s["by_status"] == {"Saved": 0, "Applied": 0, "Interview": 0, "Offer": 0, "Rejected": 0}


def test_five_applications_three_past_saved(client, auth_headers, make_app):
    for _ in range(2):
        make_app()
    for s in ("Applied", "Interview", "Rejected"):
        make_app(status=s)
    s = stats(client, auth_headers)
    assert s["total"] == 5 and s["submitted"] == 3
    assert s["by_status"] == {"Saved": 2, "Applied": 1, "Interview": 1, "Offer": 0, "Rejected": 1}


def test_all_saved_means_nothing_submitted(client, auth_headers, make_app):
    for _ in range(4):
        make_app()
    s = stats(client, auth_headers)
    assert s["total"] == 4 and s["submitted"] == 0


def test_offer_and_rejected_both_count_as_submitted(client, auth_headers, make_app):
    make_app(status="Offer")
    make_app(status="Rejected")
    assert stats(client, auth_headers)["submitted"] == 2


def test_counts_follow_add_move_delete(client, auth_headers, make_app):
    a = make_app()
    assert stats(client, auth_headers)["total"] == 1
    client.patch(f"/api/applications/{a['id']}", json={"status": "Applied"}, headers=auth_headers)
    s = stats(client, auth_headers)
    assert s["by_status"]["Saved"] == 0 and s["by_status"]["Applied"] == 1 and s["submitted"] == 1
    client.delete(f"/api/applications/{a['id']}", headers=auth_headers)
    assert stats(client, auth_headers)["total"] == 0


def test_by_status_always_sums_to_total(client, auth_headers, make_app):
    for s in ("Saved", "Saved", "Applied", "Offer", "Rejected", "Interview", "Interview"):
        make_app(status=s)
    s = stats(client, auth_headers)
    assert sum(s["by_status"].values()) == s["total"] == 7


def test_response_rate_rounds_to_whole_percent(client, auth_headers, make_app):
    def reach(app_id):
        for st in ("Applied", "Interview"):
            client.patch(f"/api/applications/{app_id}", json={"status": st}, headers=auth_headers)

    reach(make_app()["id"])
    make_app(status="Applied")
    make_app(status="Applied")
    assert stats(client, auth_headers)["response_rate"] == 33  # 1 of 3


def test_response_rate_counts_an_application_that_was_interviewed_then_rejected(client, auth_headers, make_app):
    a = make_app()
    for st in ("Applied", "Interview", "Rejected"):
        client.patch(f"/api/applications/{a['id']}", json={"status": st}, headers=auth_headers)
    assert stats(client, auth_headers)["response_rate"] == 100


def test_response_rate_ignores_applications_moved_back_to_saved(client, auth_headers, make_app):
    a = make_app()
    for st in ("Applied", "Interview", "Saved"):
        client.patch(f"/api/applications/{a['id']}", json={"status": st}, headers=auth_headers)
    s = stats(client, auth_headers)
    assert s["submitted"] == 0 and s["response_rate"] is None


# ─── US-10 next 7 days ────────────────────────────────────────────────────────

def test_follow_up_and_deadline_listed_in_date_order(client, auth_headers, make_app):
    make_app(company="Later", deadline=day(5))
    make_app(company="Sooner", follow_up_date=day(3), status="Applied")
    assert upcoming(client, auth_headers) == [("Sooner", "follow_up", False), ("Later", "deadline", False)]


def test_window_includes_today_and_day_7_but_not_day_8(client, auth_headers, make_app):
    make_app(company="Today", deadline=day(0))
    make_app(company="Day7", deadline=day(7))
    make_app(company="Day8", deadline=day(8))
    assert [c for c, _, _ in upcoming(client, auth_headers)] == ["Today", "Day7"]


def test_deadline_today_is_not_overdue_but_yesterday_is(client, auth_headers, make_app):
    make_app(company="Today", deadline=day(0))
    make_app(company="Yesterday", deadline=day(-1))
    assert upcoming(client, auth_headers) == [("Yesterday", "deadline", True), ("Today", "deadline", False)]


def test_overdue_follow_up_comes_first_and_is_flagged(client, auth_headers, make_app):
    make_app(company="Soon", deadline=day(2))
    make_app(company="Chase", follow_up_date=day(-1), status="Applied")
    assert upcoming(client, auth_headers)[0] == ("Chase", "follow_up", True)


def test_deadline_beyond_window_is_not_listed(client, auth_headers, make_app):
    make_app(deadline=day(12))
    assert stats(client, auth_headers)["upcoming"] == []


def test_closed_applications_are_never_listed_or_overdue(client, auth_headers, make_app):
    for st in ("Rejected", "Offer"):
        make_app(company=f"Closed-{st}", status=st, deadline=day(-3), follow_up_date=day(1))
    assert stats(client, auth_headers)["upcoming"] == []


def test_closed_application_interview_is_not_listed(client, auth_headers, make_app):
    soon = (datetime.now(timezone.utc) + timedelta(days=2)).replace(microsecond=0).isoformat()
    make_app(company="Rejected after interview", status="Rejected", interview_date=soon)
    make_app(company="Open", status="Interview", interview_date=soon)
    assert [c for c, _, _ in upcoming(client, auth_headers)] == ["Open"]


def test_one_application_with_deadline_and_interview_gives_two_rows(client, auth_headers, make_app):
    soon = (datetime.now(timezone.utc) + timedelta(days=4)).replace(microsecond=0).isoformat()
    make_app(company="Both", deadline=day(2), interview_date=soon, status="Applied")
    assert upcoming(client, auth_headers) == [("Both", "deadline", False), ("Both", "interview", False)]


def test_nothing_due_gives_empty_list(client, auth_headers, make_app):
    make_app()
    assert stats(client, auth_headers)["upcoming"] == []


def test_interview_beyond_window_is_not_listed(client, auth_headers, make_app):
    far = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()
    make_app(interview_date=far)
    assert stats(client, auth_headers)["upcoming"] == []


def test_upcoming_is_per_user(client, auth_headers, other_headers, make_app):
    make_app(headers=other_headers, company="Theirs", deadline=day(1))
    assert stats(client, auth_headers)["upcoming"] == []


def test_upcoming_item_carries_ids_for_linking(client, auth_headers, make_app):
    app = make_app(company="Kaspi", position="Backend Intern", deadline=day(1))
    item = stats(client, auth_headers)["upcoming"][0]
    assert item["application_id"] == app["id"] and item["position"] == "Backend Intern" and item["when"] == day(1)


def test_invalid_today_param_is_rejected(client, auth_headers):
    assert client.get("/api/dashboard/stats", params={"today": "nope"}, headers=auth_headers).status_code == 422
