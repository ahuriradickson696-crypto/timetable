"""Activities — MongoDB."""
from fastapi import APIRouter, Depends
from typing import Optional
from app.db.mongodb import activities_col
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/activities", tags=["activities"])


@router.get("")
async def list_activities(activity_type: Optional[str] = None, current=Depends(get_current_user)):
    q = {}
    if activity_type:
        q["activity_type"] = activity_type
    rows = await activities_col().find(q).to_list(1000)
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows