from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from routers import applications, auth, dashboard

# The schema is managed by Alembic:  alembic upgrade head

app = FastAPI(
    title="Internship Tracker API",
    description="Track your internship applications",
    version="1.1.0",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(applications.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"message": "Internship Tracker API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
