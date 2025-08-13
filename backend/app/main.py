"""
app/main.py
FastAPI app for the Marvel Comic Release Tracker MVP.

Endpoints:
- GET  /api/health
- GET  /api/comics                          (optional ?start=YYYY-MM-DD&end=YYYY-MM-DD)
- GET  /api/comics/search?q=term
- GET  /api/comics/{comic_id}
- GET  /api/comics/week?wed=YYYY-MM-DD      (Wed..Tue window)
- POST /api/marvel/sync?start=YYYY-MM-DD&end=YYYY-MM-DD&include_collections=bool

Notes:
- Uses robust string parsing for dates to avoid 422 errors in some environments.
- Keeps private API keys on the server; frontend talks only to these routes.
"""

from datetime import date, timedelta
from typing import List, Optional, Tuple

from fastapi import FastAPI, Query, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select

from .db import engine, init_db
from .models import Comic
from .services import sync_range_to_db


# --------------------------- FastAPI app + CORS ---------------------------

app = FastAPI(title="Comic Finder API", version="0.2.0")

# CORS: open in dev so Vite (http://localhost:5173) can call the API.
# Lock this down to your deployed domain(s) for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # e.g., ["http://localhost:5173"] for stricter dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup() -> None:
    init_db()


# --------------------------- Schemas ---------------------------

class ComicOut(BaseModel):
    id: int
    marvel_id: Optional[int] = None
    title: str
    author: Optional[str] = None
    onsale_date: Optional[date] = None
    format: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    # Marvel sometimes uses float for old issue numbers
    issue_number: Optional[float] = None

    class Config:
        from_attributes = True  # allow conversion from SQLModel/ORM objects


# --------------------------- Helpers ---------------------------

def _parse_iso_date(s: str) -> date:
    """Robust YYYY-MM-DD parser that doesn't rely on Pydantic coercion."""
    try:
        y, m, d = map(int, s.split("-"))
        return date(y, m, d)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

def wednesday_week_range(wed: date) -> Tuple[date, date]:
    """Return the Wed..Tue window for a given Wednesday date."""
    start = wed
    end = wed + timedelta(days=6)
    return start, end


# --------------------------- Routes ---------------------------

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/comics", response_model=List[ComicOut])
def list_comics(
    start: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="YYYY-MM-DD"),
) -> List[ComicOut]:
    """
    List comics, optionally filtering by on-sale date range.
    Example: /api/comics?start=2025-08-01&end=2025-08-31
    """
    start_date: Optional[date] = _parse_iso_date(start) if start else None
    end_date: Optional[date] = _parse_iso_date(end) if end else None

    with Session(engine) as session:
        stmt = select(Comic)
        if start_date:
            stmt = stmt.where(Comic.onsale_date >= start_date)
        if end_date:
            stmt = stmt.where(Comic.onsale_date <= end_date)
        stmt = stmt.order_by(Comic.onsale_date)
        return session.exec(stmt).all()


@app.get("/api/comics/search", response_model=List[ComicOut])
def search_comics(q: str = Query(..., min_length=1, description="Search term in title")) -> List[ComicOut]:
    """
    Case-insensitive search by title substring.
    Example: /api/comics/search?q=avengers
    """
    with Session(engine) as session:
        # SQLModel/SQLAlchemy ilike for case-insensitive contains
        stmt = select(Comic).where(Comic.title.ilike(f"%{q}%")).order_by(Comic.onsale_date)
        return session.exec(stmt).all()


@app.get("/api/comics/week", response_model=List[ComicOut])
def comics_by_wednesday(wed: str = Query(..., description="YYYY-MM-DD")) -> List[ComicOut]:
    """
    Return comics for the Wed..Tue window containing 'wed' (string 'YYYY-MM-DD').
    """
    wed_date = _parse_iso_date(wed)
    start, end = wednesday_week_range(wed_date)
    with Session(engine) as session:
        stmt = (
            select(Comic)
            .where(Comic.onsale_date >= start, Comic.onsale_date <= end)
            .order_by(Comic.onsale_date)
        )
        return session.exec(stmt).all()

@app.get("/api/comics/{comic_id}", response_model=ComicOut)
def get_comic(comic_id: int = Path(..., ge=1)) -> ComicOut:
    with Session(engine) as session:
        row = session.get(Comic, comic_id)
        if not row:
            raise HTTPException(status_code=404, detail="Comic not found")
        return row

@app.post("/api/marvel/sync")
def marvel_sync(
    start: str = Query(..., description="YYYY-MM-DD"),
    end: str = Query(..., description="YYYY-MM-DD"),
    include_collections: bool = Query(False, description="Include TPBs/omnibi/etc."),
) -> dict:
    """
    Server-side sync from Marvel into our DB (keeps private key secret).
    Example: POST /api/marvel/sync?start=2025-08-01&end=2025-08-31
    """
    start_date = _parse_iso_date(start)
    end_date = _parse_iso_date(end)
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="'end' must be >= 'start'")

    inserted, updated = sync_range_to_db(start_date.isoformat(), end_date.isoformat(), include_collections=include_collections)
    return {"inserted": inserted, "updated": updated}
