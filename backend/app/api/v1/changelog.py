"""Change log read endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.change_log import ChangeLog
from app.models.user import User


router = APIRouter(prefix="/changelog", tags=["changelog"])


class ChangeLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    run_id: Optional[int] = None
    details: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[ChangeLogOut])
def list_changes(
    run_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(ChangeLog).order_by(ChangeLog.timestamp.desc()).limit(limit)
    if run_id:
        stmt = stmt.where(ChangeLog.run_id == run_id)
    return list(db.scalars(stmt))