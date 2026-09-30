from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

HORIZON_DAYS = 7


@router.get("/stats", response_model=schemas.DashboardStats)
def get_stats(
    today: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """`today` is the client's local date, so "next 7 days" matches what the user sees."""
    A = models.Application
    uid = current_user.id
    now = datetime.now(timezone.utc)
    today = today or now.date()
    horizon = today + timedelta(days=HORIZON_DAYS)

    by_status = {s: 0 for s in models.STATUSES}
    rows = db.query(A.status, func.count(A.id)).filter(A.user_id == uid).group_by(A.status).all()
    for status_name, count in rows:
        by_status[status_name] = count
    total = sum(by_status.values())

    # Response rate: of everything submitted (anything past "Saved"), how much
    # ever reached an interview or an offer.
    submitted = total - by_status["Saved"]
    reached = (
        db.query(func.count(distinct(models.StatusHistory.application_id)))
        .join(A, A.id == models.StatusHistory.application_id)
        .filter(
            A.user_id == uid,
            A.status != "Saved",
            models.StatusHistory.new_status.in_(("Interview", "Offer")),
        )
        .scalar()
    )
    response_rate = round(100 * reached / submitted) if submitted else None

    active = A.status.notin_(models.CLOSED_STATUSES)
    items: list[tuple[datetime, schemas.UpcomingItem]] = []

    def add(app, kind, when, sort_at, overdue):
        items.append((sort_at, schemas.UpcomingItem(
            application_id=app.id, company=app.company, position=app.position,
            kind=kind, when=when, overdue=overdue,
        )))

    def at_midnight(d: date) -> datetime:
        return datetime.combine(d, time.min, tzinfo=timezone.utc)

    for app in db.query(A).filter(A.user_id == uid, active, A.deadline != None, A.deadline <= horizon):  # noqa: E711
        add(app, "deadline", app.deadline.isoformat(), at_midnight(app.deadline), app.deadline < today)

    for app in db.query(A).filter(A.user_id == uid, active, A.follow_up_date != None, A.follow_up_date <= horizon):  # noqa: E711
        add(app, "follow_up", app.follow_up_date.isoformat(), at_midnight(app.follow_up_date), app.follow_up_date < today)

    window_end = now + timedelta(days=HORIZON_DAYS + 1)
    for app in db.query(A).filter(A.user_id == uid, A.interview_date != None, A.interview_date >= now, A.interview_date <= window_end):  # noqa: E711
        when = app.interview_date
        when = when.replace(tzinfo=timezone.utc) if when.tzinfo is None else when.astimezone(timezone.utc)
        add(app, "interview", when.isoformat().replace("+00:00", "Z"), when, False)

    items.sort(key=lambda pair: pair[0])

    return {
        "total": total,
        "by_status": by_status,
        "submitted": submitted,
        "response_rate": response_rate,
        "upcoming": [item for _, item in items],
    }
