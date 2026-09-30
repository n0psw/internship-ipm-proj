"""Load demo data:  python seed.py

Creates demo@example.com / demo12345 with a realistic spread of applications.
Safe to run twice: it does nothing if the demo user already exists.
"""
from datetime import datetime, time, timedelta, timezone

import auth
import models
from database import SessionLocal

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo12345"


def main() -> None:
    db = SessionLocal()
    try:
        if db.query(models.User).filter_by(email=DEMO_EMAIL).first():
            print(f"{DEMO_EMAIL} already exists, nothing to do")
            return

        user = models.User(
            name="Demo Student", email=DEMO_EMAIL, password_hash=auth.hash_password(DEMO_PASSWORD)
        )
        db.add(user)
        db.flush()

        today = datetime.now(timezone.utc).date()
        day = lambda n: today + timedelta(days=n)  # noqa: E731
        at = lambda n, hour: datetime.combine(day(n), time(hour), tzinfo=timezone.utc)  # noqa: E731

        # (fields, status path). Every application gets a history row per status it went through.
        rows = [
            (dict(company="Kaspi.kz", position="Backend Intern", location="Almaty", source="LinkedIn",
                  job_url="https://kaspi.kz/careers", deadline=day(2), cv_version="CV v3 (backend)"),
             ["Saved"]),
            (dict(company="Yandex", position="Data Analyst Intern", location="Remote", source="Company website",
                  deadline=day(9), notes="Needs SQL test. Prepare window functions."),
             ["Saved"]),
            (dict(company="Google", position="SWE Intern", location="Zurich", source="Company website",
                  job_url="https://careers.google.com", deadline=day(-3), follow_up_date=day(3),
                  cv_version="CV v3 (backend)", contact_name="Anna Weber", contact_info="anna.weber@example.com"),
             ["Saved", "Applied"]),
            (dict(company="EPAM", position="QA Automation Intern", location="Astana", source="University",
                  follow_up_date=day(1), cv_version="CV v2 (general)"),
             ["Saved", "Applied"]),
            (dict(company="Kolesa Group", position="Frontend Intern", location="Almaty", source="Telegram",
                  interview_date=at(2, 10), cv_version="CV v3 (frontend)",
                  contact_name="Dias", contact_info="@dias_hr", notes="Technical interview, React basics."),
             ["Saved", "Applied", "Interview"]),
            (dict(company="Kaspi Bank", position="Risk Analyst Intern", location="Almaty", source="hh.ru",
                  interview_date=at(5, 14), cv_version="CV v2 (general)"),
             ["Applied", "Interview"]),
            (dict(company="JetBrains", position="Kotlin Intern", location="Remote", source="Referral",
                  cv_version="CV v3 (backend)", notes="Offer expires in two weeks."),
             ["Saved", "Applied", "Interview", "Offer"]),
            (dict(company="Beeline", position="DevOps Intern", location="Almaty", source="hh.ru"),
             ["Saved", "Applied", "Rejected"]),
        ]

        for fields, path in rows:
            app = models.Application(user_id=user.id, status=path[-1], **fields)
            db.add(app)
            db.flush()
            start = datetime.now(timezone.utc) - timedelta(days=len(path) * 3)
            previous = None
            for i, status in enumerate(path):
                db.add(models.StatusHistory(
                    application_id=app.id, old_status=previous, new_status=status,
                    changed_at=start + timedelta(days=i * 3),
                ))
                previous = status

        db.commit()
        print(f"Created {DEMO_EMAIL} / {DEMO_PASSWORD} with {len(rows)} applications")
    finally:
        db.close()


if __name__ == "__main__":
    main()
