import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "change-me":
    raise RuntimeError(
        "SECRET_KEY is not set. Copy .env.example to .env and set a random value."
    )

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./internship_tracker.db")
# Some hosts still hand out the legacy "postgres://" scheme, which SQLAlchemy rejects.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
JWT_ALGORITHM = "HS256"
