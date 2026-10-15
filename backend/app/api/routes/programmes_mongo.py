"""Programmes — MongoDB."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.db.mongodb import programmes_col
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/programmes", tags=["programmes"])


class ProgrammeCreate(BaseModel):
    code: str
    name: str
    level: str
    school_faculty: str
    duration_years: int = 3
    active: bool = True
    notes: Optional[str] = ""


@router.get("")
async def list_programmes(current=Depends(get_current_user)):
    rows = await programmes_col().find().sort("code", 1).to_list(500)
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows


@router.get("/{code}")
async def get_programme(code: str, current=Depends(get_current_user)):
    r = await programmes_col().find_one({"code": code})
    if not r:
        raise HTTPException(404, "Programme not found")
    r["_id"] = str(r["_id"])
    return r


@router.post("", status_code=201)
async def create_programme(body: ProgrammeCreate, current=Depends(get_current_user)):
    if await programmes_col().find_one({"code": body.code}):
        raise HTTPException(409, "Programme already exists")
    doc = body.model_dump()
    result = await programmes_col().insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc