"""Pydantic request/response models."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    is_admin: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class BookingCreate(BaseModel):
    # Free-text time slot for simplicity, e.g. "10am-11am".
    time_slot: str = Field(..., min_length=1, max_length=100)


class BookingUpdate(BaseModel):
    time_slot: str = Field(..., min_length=1, max_length=100)


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    time_slot: str
    created_at: datetime
