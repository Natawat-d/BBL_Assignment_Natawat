"""Booking management endpoints with ownership/admin authorization.

Authorization rules:
- ``GET /api/bookings`` returns *all* bookings for admins, but only the caller's
  own bookings for regular users.
- A regular user may only read/update/delete their own bookings. Accessing a
  booking they don't own returns 404 so existence isn't leaked.
- An admin may manage any booking.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, models
from ..db import get_db
from ..schemas import BookingCreate, BookingOut, BookingUpdate
from ..security import get_current_user

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def _get_owned_or_404(
    db: Session, booking_id: int, current_user: models.User
) -> models.Booking:
    """Fetch a booking the user is allowed to access, else raise 404.

    Admins can access any booking; regular users only their own. We use 404
    (not 403) for another user's booking to avoid revealing that it exists.
    """
    booking = crud.get_booking(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if not current_user.is_admin and booking.username != current_user.username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


@router.get("", response_model=list[BookingOut])
def list_bookings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> list[models.Booking]:
    """List bookings: all for admins, only the caller's own for regular users."""
    if current_user.is_admin:
        return crud.list_bookings(db)
    return crud.list_bookings(db, username=current_user.username)


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Booking:
    """Create a booking owned by the current user."""
    return crud.create_booking(db, current_user.username, payload.time_slot)


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Booking:
    """Fetch a single booking (owner or admin only)."""
    return _get_owned_or_404(db, booking_id, current_user)


@router.put("/{booking_id}", response_model=BookingOut)
def update_booking(
    booking_id: int,
    payload: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Booking:
    """Update a booking's time slot (owner or admin only)."""
    booking = _get_owned_or_404(db, booking_id, current_user)
    return crud.update_booking(db, booking, payload.time_slot)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> None:
    """Delete a booking (owner or admin only)."""
    booking = _get_owned_or_404(db, booking_id, current_user)
    crud.delete_booking(db, booking)
