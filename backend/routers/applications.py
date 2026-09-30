from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/applications", tags=["applications"])


def _like(term: str) -> str:
    """Escape LIKE wildcards so user input is matched literally."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _get_owned(db: Session, app_id: int, user: models.User) -> models.Application:
    app = (
        db.query(models.Application)
        .filter(models.Application.id == app_id, models.Application.user_id == user.id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.get("", response_model=list[schemas.ApplicationOut])
def list_applications(
    status: Optional[schemas.Status] = None,
    search: Optional[str] = None,
    location: Optional[str] = None,
    deadline_from: Optional[date] = None,
    deadline_to: Optional[date] = None,
    sort: Literal["created_at", "deadline", "company"] = "created_at",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    A = models.Application
    q = db.query(A).filter(A.user_id == current_user.id)

    if status:
        q = q.filter(A.status == status)
    if location:
        q = q.filter(A.location.ilike(_like(location.strip()), escape="\\"))
    if search:
        term = _like(search.strip())
        q = q.filter(or_(A.company.ilike(term, escape="\\"), A.position.ilike(term, escape="\\")))
    if deadline_from:
        q = q.filter(A.deadline >= deadline_from)
    if deadline_to:
        q = q.filter(A.deadline <= deadline_to)

    if sort == "deadline":
        q = q.order_by(A.deadline.asc().nullslast(), A.id.desc())
    elif sort == "company":
        q = q.order_by(A.company.asc(), A.id.desc())
    else:
        q = q.order_by(A.created_at.desc(), A.id.desc())

    return q.all()


@router.post("", response_model=schemas.ApplicationOut, status_code=201)
def create_application(
    data: schemas.ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    app = models.Application(user_id=current_user.id, **data.model_dump())
    db.add(app)
    db.flush()
    db.add(models.StatusHistory(application_id=app.id, old_status=None, new_status=app.status))
    db.commit()
    db.refresh(app)
    return app


@router.get("/{app_id}", response_model=schemas.ApplicationOut)
def get_application(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return _get_owned(db, app_id, current_user)


@router.patch("/{app_id}", response_model=schemas.ApplicationOut)
def update_application(
    app_id: int,
    data: schemas.ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    app = _get_owned(db, app_id, current_user)

    update_data = data.model_dump(exclude_unset=True)
    old_status = app.status
    for field, value in update_data.items():
        setattr(app, field, value)

    if "status" in update_data and update_data["status"] != old_status:
        db.add(
            models.StatusHistory(
                application_id=app.id, old_status=old_status, new_status=update_data["status"]
            )
        )

    db.commit()
    db.refresh(app)
    return app


@router.delete("/{app_id}")
def delete_application(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    app = _get_owned(db, app_id, current_user)
    db.delete(app)
    db.commit()
    return {"message": "Deleted", "id": app_id}


@router.get("/{app_id}/history", response_model=list[schemas.StatusHistoryOut])
def get_history(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    _get_owned(db, app_id, current_user)
    return (
        db.query(models.StatusHistory)
        .filter(models.StatusHistory.application_id == app_id)
        .order_by(models.StatusHistory.changed_at.desc(), models.StatusHistory.id.desc())
        .all()
    )
