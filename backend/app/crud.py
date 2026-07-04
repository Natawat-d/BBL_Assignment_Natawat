"""Database access helpers (CRUD) and password utilities.

Keeping query logic here keeps the routers thin and makes the authorization
rules in the routers easy to read.
"""
from typing import Optional

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models

# Demo accounts seeded on startup. Passwords are documented in the README.
DEFAULT_USERS = [
    ("admin", "admin123", True),
    ("alice", "alice123", False),
    ("bob", "bob123", False),
]


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt, returning a str for storage."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def seed_default_users(db: Session) -> None:
    """Insert the demo users if they don't already exist (idempotent).

    Intended for local development only — gated behind SEED_DEMO_USERS.
    """
    for username, password, is_admin in DEFAULT_USERS:
        if get_user(db, username) is None:
            db.add(
                models.User(
                    username=username,
                    password_hash=hash_password(password),
                    is_admin=is_admin,
                )
            )
    db.commit()


def ensure_admin(db: Session, username: str, password: str) -> None:
    """Create an admin account from provided credentials if it doesn't exist.

    Used to bootstrap the first admin in production without shipping default
    credentials in the codebase.
    """
    if get_user(db, username) is None:
        db.add(
            models.User(
                username=username,
                password_hash=hash_password(password),
                is_admin=True,
            )
        )
        db.commit()


def get_user(db: Session, username: str) -> Optional[models.User]:
    return db.scalar(select(models.User).where(models.User.username == username))


def authenticate(db: Session, username: str, password: str) -> Optional[models.User]:
    """Return the user if credentials are valid, else None."""
    user = get_user(db, username)
    if user and verify_password(password, user.password_hash):
        return user
    return None


def create_booking(db: Session, username: str, time_slot: str) -> models.Booking:
    booking = models.Booking(username=username, time_slot=time_slot)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_booking(db: Session, booking_id: int) -> Optional[models.Booking]:
    return db.get(models.Booking, booking_id)


def list_bookings(db: Session, username: Optional[str] = None) -> list[models.Booking]:
    """List bookings, optionally filtered to a single owner.

    ``username=None`` returns every booking (admin view).
    """
    stmt = select(models.Booking).order_by(models.Booking.id)
    if username is not None:
        stmt = stmt.where(models.Booking.username == username)
    return list(db.scalars(stmt))


def update_booking(db: Session, booking: models.Booking, time_slot: str) -> models.Booking:
    booking.time_slot = time_slot
    db.commit()
    db.refresh(booking)
    return booking


def delete_booking(db: Session, booking: models.Booking) -> None:
    db.delete(booking)
    db.commit()
