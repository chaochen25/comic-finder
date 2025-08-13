"""
React server can call the API from a different port: 
- /api/health route for checks
- A /api/comics/search route
- A /api/comics route date filtering.
"""
from datetime import date
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from pydantic import BaseModel

from .db import engine, init_db
from .models import Comic

app = FastAPI(title="Comic Finder API", version="0.1.0")

# CORS: allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # make sure tables exist
    init_db()

@app.get("/api/health")
def health():
    """Quick check route."""
    return {"status": "ok"}

class ComicOut(BaseModel):
    """Pydantic schema for API responses."""
    id: int
    title: str
    author: Optional[str] = None
    onsale_date: Optional[date] = None
    format: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True 

@app.get("/api/comics/search", response_model=List[ComicOut])
def search_comics(q: str = Query(..., min_length=1, description="Search term in title")):
    """
    Search by title substring (case-insensitive).
    Example: /api/comics/search?q=batman
    """
    with Session(engine) as session:
        statement = select(Comic).where(Comic.title.ilike(f"%{q}%"))
        results = session.exec(statement).all()
        return results

@app.get("/api/comics", response_model=List[ComicOut])
def list_comics(
    start: Optional[date] = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end: Optional[date] = Query(None, description="Filter end date (YYYY-MM-DD)")
):
    """
    List comics, optionally filtering by on-sale date range.
    Example: /api/comics?start=2025-08-01&end=2025-08-31
    """
    with Session(engine) as session:
        statement = select(Comic)
        if start:
            statement = statement.where(Comic.onsale_date >= start)
        if end:
            statement = statement.where(Comic.onsale_date <= end)
        results = session.exec(statement).all()
        return results

from fastapi import HTTPException
from datetime import timedelta
from .services import sync_range_to_db
from fastapi import HTTPException, Path

@app.get("/api/comics/{comic_id}", response_model=ComicOut)
def get_comic(comic_id: int = Path(..., ge=1)):
    with Session(engine) as session:
        row = session.get(Comic, comic_id)
        if not row:
            raise HTTPException(status_code=404, detail="Comic not found")
        return row

def wednesday_week_range(wed: date) -> tuple[date, date]:
    start = wed
    end = wed + timedelta(days=6)  # Wed..Tue
    return start, end

@app.post("/api/marvel/sync")
def marvel_sync(start: date, end: date, include_collections: bool = False):
    """
    Server-side sync from Marvel into our DB (safe: keeps your private key hidden).
    Example call:
      POST /api/marvel/sync?start=2025-08-01&end=2025-08-31
    """
    if end < start:
        raise HTTPException(status_code=400, detail="end must be >= start")
    inserted, updated = sync_range_to_db(start.isoformat(), end.isoformat(), include_collections=include_collections)
    return {"inserted": inserted, "updated": updated}

@app.get("/api/comics/week", response_model=List[ComicOut])
def comics_by_wednesday(wed: date):
    """
    Returns comics for the Wed..Tue window containing 'wed'.
    """
    start, end = wednesday_week_range(wed)
    with Session(engine) as session:
        stmt = select(Comic).where(Comic.onsale_date >= start, Comic.onsale_date <= end).order_by(Comic.onsale_date)
        return session.exec(stmt).all()
