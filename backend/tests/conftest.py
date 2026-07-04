"""Pytest fixtures.

Tests run against a real PostgreSQL database (per the project's Docker-based
setup). Point ``DATABASE_URL`` at the test database before running, e.g.:

    DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/appointments_test pytest

The schema is created once per session and every table is truncated and reseeded
before each test so cases stay isolated.
"""
import pytest
from sqlalchemy import text

from app import crud, models  # noqa: F401  (import registers models on Base)
from app.db import Base, SessionLocal, engine


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_db():
    """Truncate tables and reseed demo users before each test."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE bookings, users RESTART IDENTITY CASCADE"))
    with SessionLocal() as db:
        crud.seed_default_users(db)
    yield
