# backend/app/services.py (additions for ComicVine)
from typing import Tuple, Optional, List, Dict, Any
from datetime import date
from sqlmodel import Session, select
from .db import engine
from .models import Comic
from .comicvine_client import fetch_issues_by_date_range, fetch_volumes_by_ids

def _safe_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        y, m, d = map(int, s[:10].split("-"))
        return date(y, m, d)
    except Exception:
        return None

def _first_writer_name(issue: Dict[str, Any]) -> Optional[str]:
    """
    ComicVine person_credits isn’t returned unless requested; we didn’t include it to keep payloads small.
    You can enhance this later by adding person_credits to field_list and scanning for role 'writer'.
    """
    return None

def _best_title(issue: Dict[str, Any]) -> str:
    vol = (issue.get("volume") or {}).get("name")
    name = issue.get("name")
    num = issue.get("issue_number")
    if vol and num not in (None, ""):
        try:
            n = int(float(str(num)))
            return f"{vol} #{n}"
        except Exception:
            return f"{vol} #{num}"
    return name or "Untitled"

def _best_thumb(issue: Dict[str, Any]) -> Optional[str]:
    img = issue.get("image") or {}
    return img.get("small_url") or img.get("thumb_url") or img.get("icon_url") or img.get("medium_url") or img.get("super_url")

def _best_description(issue: Dict[str, Any]) -> Optional[str]:
    # prefer long description, fallback to short deck
    desc = issue.get("description")
    if isinstance(desc, str) and desc.strip():
        return desc.strip()
    deck = issue.get("deck")
    if isinstance(deck, str) and deck.strip():
        return deck.strip()
    return None

def _map_cv_issue_to_comic(issue: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    ext_id = issue.get("id")  # ComicVine issue id
    doc = {
        "title": _best_title(issue),
        "author": _first_writer_name(issue),
        "onsale_date": _safe_date(issue.get("cover_date") or issue.get("store_date")),
        "format": "Comic",
        "thumbnail_url": _best_thumb(issue),
        "description": _best_description(issue),
        "issue_number": issue.get("issue_number"),
        "marvel_id": ext_id,  # reuse as external_id
    }
    return doc, ext_id

def cv_sync_range_to_db(start_iso: str, end_iso: str, include_collections: bool = False) -> Tuple[int, int]:
    """
    Pull issues from ComicVine for [start_iso, end_iso], filter to Marvel publisher,
    and upsert into our Comic table by external id.
    """
    inserted = updated = 0
    offset = 0
    limit = 100

    with Session(engine) as session:
        while True:
            payload = fetch_issues_by_date_range(start_iso, end_iso, limit=limit, offset=offset)
            results: List[Dict[str, Any]] = payload.get("results", [])
            total = payload.get("number_of_total_results", 0)

            # Map volume_id -> publisher so we can filter to Marvel only
            vol_ids = [ (it.get("volume") or {}).get("id") for it in results if (it.get("volume") or {}).get("id") ]
            vol_ids = list(dict.fromkeys(vol_ids))  # unique, keep order
            vol_map = fetch_volumes_by_ids(vol_ids) if vol_ids else {}

            for issue in results:
                vol = issue.get("volume") or {}
                vol_pub_name = None
                vol_info = vol_map.get(vol.get("id"))
                if vol_info and isinstance(vol_info.get("publisher"), dict):
                    vol_pub_name = (vol_info["publisher"].get("name") or "").strip()

                # Keep only Marvel
                if vol_pub_name and vol_pub_name.lower() != "marvel":
                    continue

                doc, ext_id = _map_cv_issue_to_comic(issue)
                if not ext_id:
                    continue

                existing = session.exec(select(Comic).where(Comic.marvel_id == ext_id)).first()
                if existing:
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

# --- compatibility shim (Marvel -> ComicVine) ---
def sync_range_to_db(start_iso: str, end_iso: str, include_collections: bool = False):
    """
    Backward-compat shim so old imports keep working.
    Routes should prefer /api/cv/sync (cv_sync_range_to_db), but this
    lets /api/marvel/sync keep functioning if it's still referenced.
    """
    return cv_sync_range_to_db(start_iso, end_iso, include_collections=include_collections)

