"""FastAPI application entry point.

On startup it ensures the schema exists and seeds the demo users. It retries the
initial DB connection briefly so the app can start alongside Postgres in Docker.
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from . import crud, models  # noqa: F401  (models imported so tables register)
from .config import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    CORS_ORIGINS,
    SEED_DEMO_USERS,
    validate_config,
)
from .db import Base, SessionLocal, engine
from .routers import auth, bookings


def _wait_for_db(retries: int = 10, delay: float = 1.5) -> None:
    """Block until the database accepts connections (handles Docker startup)."""
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == retries:
                raise
            time.sleep(delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast on insecure production config, then prepare the database.
    validate_config()
    _wait_for_db()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if SEED_DEMO_USERS:
            crud.seed_default_users(db)
        if ADMIN_USERNAME and ADMIN_PASSWORD:
            crud.ensure_admin(db, ADMIN_USERNAME, ADMIN_PASSWORD)
    yield


app = FastAPI(
    title="Appointment Booking API",
    description=(
        "Log in and manage appointment bookings. Admins can view all "
        "appointments; regular users manage only their own."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(bookings.router)


@app.get("/api/health", tags=["health"])
def health() -> dict:
    """Simple liveness probe."""
    return {"status": "ok"}
