from datetime import date, datetime, timezone
import re
from typing import Annotated, Literal, Optional
from urllib.parse import urlparse

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    PlainSerializer,
    StringConstraints,
    field_validator,
    model_validator,
)

from models import STATUSES

Status = Literal[STATUSES]


# ─── Shared types ─────────────────────────────────────────────────────────────

def _to_utc(v: datetime) -> datetime:
    """Naive datetimes (SQLite drops tzinfo) are treated as UTC."""
    if v.tzinfo is None:
        return v.replace(tzinfo=timezone.utc)
    return v.astimezone(timezone.utc)


# Always leaves the API as ISO-8601 UTC with a trailing "Z", so the browser
# can convert it to the user's own time zone.
UTCDateTime = Annotated[
    datetime,
    AfterValidator(_to_utc),
    PlainSerializer(
        lambda v: _to_utc(v).isoformat().replace("+00:00", "Z"), return_type=str, when_used="json"
    ),
]

Required200 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


def _optional_text(max_length: int):
    return Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=max_length)]]


# ─── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v):
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_rules(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v.encode()) > 72:  # bcrypt ignores everything past 72 bytes
            raise ValueError("Password must be at most 72 bytes")
        return v


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v):
        return v.strip().lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    created_at: UTCDateTime


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# ─── Applications ─────────────────────────────────────────────────────────────

class _ApplicationFields(BaseModel):
    """Optional free-text fields shared by create and update."""

    job_url: _optional_text(500) = None
    location: _optional_text(200) = None
    source: _optional_text(100) = None
    contact_name: _optional_text(200) = None
    contact_info: _optional_text(300) = None
    cv_version: _optional_text(200) = None
    notes: _optional_text(10000) = None
    deadline: Optional[date] = None
    follow_up_date: Optional[date] = None
    interview_date: Optional[UTCDateTime] = None

    @field_validator("job_url", "location", "source", "contact_name", "contact_info", "cv_version", "notes")
    @classmethod
    def blank_to_none(cls, v):
        return v or None

    @field_validator("job_url")
    @classmethod
    def http_url_only(cls, v):
        if v is None:
            return v
        # "host:8080/path" is a port, "javascript:..." / "mailto:..." is a scheme.
        if "://" not in v:
            if re.match(r"^[a-z][a-z0-9+.-]*:(?!\d)", v, re.IGNORECASE):
                raise ValueError("Job URL must be a valid http or https link")
            v = "https://" + v
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("Job URL must be a valid http or https link")
        return v


class ApplicationCreate(_ApplicationFields):
    company: Required200
    position: Required200
    status: Status = "Saved"


class ApplicationUpdate(_ApplicationFields):
    company: Optional[Required200] = None
    position: Optional[Required200] = None
    status: Optional[Status] = None

    @model_validator(mode="after")
    def required_fields_not_null(self):
        for name in ("company", "position", "status"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    company: str
    position: str
    job_url: Optional[str]
    location: Optional[str]
    source: Optional[str]
    status: str
    deadline: Optional[date]
    follow_up_date: Optional[date]
    interview_date: Optional[UTCDateTime]
    contact_name: Optional[str]
    contact_info: Optional[str]
    cv_version: Optional[str]
    notes: Optional[str]
    created_at: UTCDateTime
    updated_at: UTCDateTime


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    old_status: Optional[str]
    new_status: str
    changed_at: UTCDateTime


# ─── Dashboard ────────────────────────────────────────────────────────────────

class UpcomingItem(BaseModel):
    application_id: int
    company: str
    position: str
    kind: Literal["deadline", "follow_up", "interview"]
    when: str  # YYYY-MM-DD for dates, UTC ISO timestamp for interviews
    overdue: bool


class DashboardStats(BaseModel):
    total: int
    by_status: dict[str, int]
    submitted: int
    response_rate: Optional[int]  # percent, None until something has been submitted
    upcoming: list[UpcomingItem]
