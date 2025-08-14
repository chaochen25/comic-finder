#main.py
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select

from .db import engine
from .models import Comic
from .services import cv_sync_range_to_db 

#created FastAPI instance
app = FastAPI(title="Comic Finder API")

#CORS for origins during local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#helper func
#parse date (ie. 2025-09-06) into a date obj
def _d(iso: str) -> date:
    try:
        y, m, d = map(int, iso.split("-"))
        return date(y, m, d)
    except Exception:
        raise HTTPException(status_code=422, detail=f"Invalid date: {iso}. Use YYYY-MM-DD")
#week length (start on Wednesday and end Tuesdays)
def _week_window(wed: date) -> tuple[date, date]:
    start = wed
    end = wed + timedelta(days=6)
    return start, end
#return month
def _month_window(d: date) -> tuple[date, date]:
    first = d.replace(day=1)
    if first.month == 12:
        next_first = first.replace(year=first.year + 1, month=1, day=1)
    else:
        next_first = first.replace(month=first.month + 1, day=1)
    last = next_first - timedelta(days=1)
    return first, last



#Models
class ComicOut(BaseModel):
    id: int
    marvel_id: Optional[int]
    title: str
    author: Optional[str] = None
    onsale_date: Optional[date] = None
    format: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


#routes
@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/comics", response_model=List[ComicOut])
def list_comics(
    start: Optional[str] = None,
    end: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    #finds a paginated list of comic books with the ablility to filter by date and title
    with Session(engine) as s:
        stmt = select(Comic)
        if start and end:
            sd, ed = _d(start), _d(end)
            stmt = stmt.where(Comic.onsale_date >= sd, Comic.onsale_date <= ed)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(Comic.title.ilike(like))
        stmt = stmt.order_by(Comic.onsale_date, Comic.title).offset(offset).limit(limit)
        rows = s.exec(stmt).all()
        return rows
#gets comics for each week
#syncs to current month if data DNE
@app.get("/api/comics/week", response_model=List[ComicOut])
def comics_week(wed: str):
    wed_d = _d(wed)
    start, end = _week_window(wed_d)

    def _query_week():
        with Session(engine) as s:
            stmt = (
                select(Comic)
                .where(Comic.onsale_date >= start, Comic.onsale_date <= end)
                .order_by(Comic.onsale_date, Comic.title)
            )
            return s.exec(stmt).all()
    rows = _query_week()
    if rows:
        return rows
    mstart, mend = _month_window(wed_d)
    try:
        cv_sync_range_to_db(mstart.isoformat(), mend.isoformat())
    except Exception as e:
        print("Auto-sync failed:", repr(e))
    return _query_week()
#used during testing to sync data
@app.post("/api/cv/sync")
def cv_sync(start: str, end: str):
    sd, ed = _d(start), _d(end)
    inserted, updated = cv_sync_range_to_db(sd.isoformat(), ed.isoformat())
    return {"inserted": inserted, "updated": updated}
#search comics from newest to oldest
@app.get("/api/comics/search", response_model=List[ComicOut])
def search(q: str, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    with Session(engine) as s:
        like = f"%{q.strip()}%"
        stmt = (
            select(Comic)
            .where(Comic.title.ilike(like))
            .order_by(Comic.onsale_date.desc(), Comic.title)
            .offset(offset)
            .limit(limit)
        )
        return s.exec(stmt).all()
