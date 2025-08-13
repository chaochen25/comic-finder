# backend/app/services.py
from typing import Tuple
from datetime import date
from sqlmodel import Session, select
from .db import engine
from .models import Comic
from .marvel_client import fetch_comics_by_date_range, build_thumbnail_url, pick_description

def _parse_onsale_date(dates: list) -> date | None:
    """
    Safely parse Marvel 'onsaleDate' strings. We only need YYYY-MM-DD,
    so slice the first 10 chars to avoid timezone/offset issues.
    """
    for item in (dates or []):
        if item.get("type") == "onsaleDate" and item.get("date"):
            s = str(item["date"])
            if len(s) >= 10:
                try:
                    y, m, d = map(int, s[:10].split("-"))
                    return date(y, m, d)
                except Exception:
                    return None
    return None

def _map_marvel_to_comic(row: dict) -> Tuple[dict, int]:
    """
    Convert a Marvel API comic dict -> fields for our Comic model and the marvel_id.
    """
    mid = row.get("id")
    title = row.get("title") or ""
    author = None
    # Pull first creator of type "writer" if available
    creators = ((row.get("creators") or {}).get("items")) or []
    for c in creators:
        if (c.get("role") or "").lower() == "writer":
            author = c.get("name")
            break

    onsale = _parse_onsale_date(row.get("dates") or [])
    fmt = row.get("format")  # e.g., "Comic", "Trade Paperback"
    thumb = build_thumbnail_url(row, variant="portrait_uncanny")
    desc = pick_description(row)
    issue_number = row.get("issueNumber")

    data = {
        "title": title,
        "author": author,
        "onsale_date": onsale,
        "format": fmt,
        "thumbnail_url": thumb,
        "description": desc,
        "issue_number": issue_number,
        "marvel_id": mid,
    }
    return data, mid

def sync_range_to_db(start_iso: str, end_iso: str, include_collections: bool = False) -> Tuple[int, int]:
    """
    Pulls all comics in [start_iso, end_iso] from Marvel and upserts them by marvel_id.
    Returns (inserted, updated).
    """
    inserted = updated = 0
    offset = 0
    limit = 100

    with Session(engine) as session:
        while True:
            payload = fetch_comics_by_date_range(start_iso, end_iso, limit=limit, offset=offset, include_collections=include_collections)
            data = (payload or {}).get("data") or {}
            results = data.get("results") or []
            total = data.get("total") or 0

            for item in results:
                doc, mid = _map_marvel_to_comic(item)
                if not mid:
                    continue
                existing = session.exec(select(Comic).where(Comic.marvel_id == mid)).first()
                if existing:
                    # Update fields (overwrite with latest)
                    for k, v in doc.items():
                        setattr(existing, k, v)
                    updated += 1
                else:
                    session.add(Comic(**doc))
                    inserted += 1

            session.commit()
            offset += limit
            if offset >= total:
                break

    return inserted, updated
