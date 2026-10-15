"""Helper to write to the change log."""
import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.change_log import ChangeLog


def log_change(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    user_id: Optional[int] = None,
    run_id: Optional[int] = None,
    details: Optional[Any] = None,
) -> None:
    entry = ChangeLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        run_id=run_id,
        details=json.dumps(details) if details is not None else None,
    )
    db.add(entry)