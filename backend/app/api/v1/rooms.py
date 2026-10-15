"""Room CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer
from app.models.room import Room
from app.models.user import User
from app.schemas.room import RoomCreate, RoomUpdate, RoomOut
from app.schemas.common import Message


router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomOut])
def list_rooms(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list(db.scalars(select(Room).order_by(Room.code)))


@router.get("/{code}", response_model=RoomOut)
def get_room(
    code: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obj = db.get(Room, code)
    if not obj:
        raise HTTPException(404, "Room not found")
    return obj


@router.post("", response_model=RoomOut, status_code=201)
def create_room(
    body: RoomCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    if db.get(Room, body.code):
        raise HTTPException(400, f"Room {body.code} already exists")
    obj = Room(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/{code}", response_model=RoomOut)
def update_room(
    code: str,
    body: RoomUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(Room, code)
    if not obj:
        raise HTTPException(404, "Room not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{code}", response_model=Message)
def delete_room(
    code: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(Room, code)
    if not obj:
        raise HTTPException(404, "Room not found")
    db.delete(obj)
    db.commit()
    return Message(detail=f"Room {code} deleted")
