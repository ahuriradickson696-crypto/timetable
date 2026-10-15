"""Room schemas."""
from pydantic import BaseModel
from typing import Optional
from app.schemas.common import ORMModel


class RoomBase(BaseModel):
    code: str
    name: str
    capacity: int
    room_type: str
    building: Optional[str] = None
    features: Optional[str] = None
    available_modes: str = "Both"
    active: bool = True
    notes: Optional[str] = None


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    room_type: Optional[str] = None
    building: Optional[str] = None
    features: Optional[str] = None
    available_modes: Optional[str] = None
    active: Optional[bool] = None
    notes: Optional[str] = None


class RoomOut(RoomBase, ORMModel):
    pass
