import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Vercel Marketplace (Neon, etc.) often injects POSTGRES_URL instead of DATABASE_URL.
DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRES_PRISMA_URL")
    or os.getenv("DATABASE_URL_UNPOOLED")
    or os.getenv("POSTGRES_URL_NON_POOLING")
    or "sqlite:///./internship_tracker.db"
)


def get_secret_key() -> str:
    key = os.getenv("SECRET_KEY")
    if not key or key == "change-me":
        raise RuntimeError(
            "SECRET_KEY is not set. Copy .env.example to .env and set a random value."
        )
    return key
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
