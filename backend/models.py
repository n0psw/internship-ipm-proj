from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base

STATUSES = ("Saved", "Applied", "Interview", "Offer", "Rejected")
CLOSED_STATUSES = ("Offer", "Rejected")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    applications = relationship("Application", back_populates="owner", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company = Column(String(200), nullable=False)
    position = Column(String(200), nullable=False)
    job_url = Column(String(500), nullable=True)
    location = Column(String(200), nullable=True)
    source = Column(String(100), nullable=True)
    status = Column(String(20), default="Saved", nullable=False)
    deadline = Column(Date, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    interview_date = Column(DateTime(timezone=True), nullable=True)
    contact_name = Column(String(200), nullable=True)
    contact_info = Column(String(300), nullable=True)
    cv_version = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    owner = relationship("User", back_populates="applications")
    history = relationship("StatusHistory", back_populates="application", cascade="all, delete-orphan")


class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    application = relationship("Application", back_populates="history")
