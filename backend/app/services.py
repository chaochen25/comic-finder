from datetime import datetime
from typing import List, Tuple
from sqlmodel import Session, select
from .db import engine
from .models import Comic
from .marvel_client import fetch_comics_by_date_range
from datetime import date
from typing import Optional

def _parse_onsale_date(dates: list) -> Optional[date]:
    """
    Marvel 'onsaleDate' strings often end with offsets like '-0400' (no colon),
    which breaks datetime.fromisoformat. For our needs, we only need the date.
    Safest approach: take the first 10 characters 'YYYY-MM-DD'.
    """
    for item in dates or []:
        if item.get("type") == "onsaleDate" and item.get("date"):
            s = str(item["date"])
            if len(s) >= 10:
                ymd = s[:10]
                try:
                    y, m, d = map(int, ymd.split("-"))
                    return date(y, m, d)
                except Exception:
                    return None
    return None

def _first_creator(creators: dict, role: str) -> str | None:
    for c in (creators or {}).get("items", []):
        if c.get("role") == role:
            return c.get("name")
    return None

def _thumb_url(thumbnail: dict) -> str | None:
    if not thumbnail: return None
    path, ext = thumbnail.get("path"), thumbnail.get("extension")
    if not path or not ext: return None
    # Marvel allows variants like /portrait_xlarge, /standard_fantastic, etc.
    return f"{path}/portrait_xlarge.{ext}"

def sync_range_to_db(start_iso: str, end_iso: str, include_collections: bool=False) -> tuple[int,int]:
    """
    Fetches all comics in [start_iso, end_iso] and upserts them into SQLite.
    Returns (inserted_count, updated_count).
    """
    inserted = updated = 0
    offset = 0
    limit = 100

    with Session(engine) as session:
        while True:
            payload = fetch_comics_by_date_range(start_iso, end_iso, limit=limit, offset=offset, include_collections=include_collections)
            data = payload.get("data", {})
            results = data.get("results", []) or []
            total = data.get("total", 0)
            count = data.get("count", 0)

            for item in results:
                mid = item.get("id")
                title = item.get("title")
                issue_number = item.get("issueNumber")
                desc = item.get("description")
                onsale = _parse_onsale_date(item.get("dates"))
                fmt = item.get("format")
                thumb = _thumb_url(item.get("thumbnail"))
                # pick a "writer" if available; fallback to first listed creator
                writer = _first_creator(item.get("creators"), "writer") or _first_creator(item.get("creators"), "editor") or None

                existing = session.exec(select(Comic).where(Comic.marvel_id == mid)).first()
                if existing:
                    # update
                    existing.title = title or existing.title
                    existing.issue_number = issue_number or existing.issue_number
                    existing.description = desc or existing.description
                    existing.onsale_date = onsale or existing.onsale_date
                    existing.format = fmt or existing.format
                    existing.thumbnail_url = thumb or existing.thumbnail_url
                    existing.author = writer or existing.author
                    updated += 1
                else:
                    session.add(Comic(
                        marvel_id=mid,
                        title=title or "Untitled",
                        issue_number=issue_number,
                        description=desc,
                        onsale_date=onsale,
                        format=fmt,
                        thumbnail_url=thumb,
                        author=writer,
                    ))
                    inserted += 1

            session.commit()

            if offset + count >= total or count == 0:
                break
            offset += count

    return inserted, updated
