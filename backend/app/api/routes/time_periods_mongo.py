"""Time Periods — MongoDB."""
from fastapi import APIRouter, Depends
from app.db.mongodb import time_periods_col
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/time-periods", tags=["time_periods"])


@router.get("")
async def list_periods(current=Depends(get_current_user)):
    rows = await time_periods_col().find().sort("order_index", 1).to_list(500)
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows