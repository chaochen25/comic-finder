"""
main.py
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
    """Pydantic schema for API responses (keeps output shape stable)."""
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
