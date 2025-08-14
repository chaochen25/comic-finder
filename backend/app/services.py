# backend/app/services.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from datetime import date

from sqlmodel import Session, select
from .db import engine
from .models import Comic
from .comicvine_client import fetch_issues_by_date_range, fetch_volumes_by_ids, CVError

def _safe_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        y, m, d = map(int, s[:10].split("-"))
        return date(y, m, d)
    except Exception:
        return None

def _best_title(issue: Dict[str, Any]) -> str:
    vol_name = (issue.get("volume") or {}).get("name")
    name = issue.get("name")
    num = issue.get("issue_number")
    if vol_name and num not in (None, ""):
        try:
            n = int(float(str(num)))
            return f"{vol_name} #{n}"
        except Exception:
            return f"{vol_name} #{num}"
    return name or "Untitled"

def _best_thumb(issue: Dict[str, Any]) -> Optional[str]:
    img = issue.get("image") or {}
    return (
        img.get("small_url")
        or img.get("thumb_url")
        or img.get("icon_url")
        or img.get("medium_url")
        or img.get("super_url")
    )

def _best_description(issue: Dict[str, Any]) -> Optional[str]:
    desc = issue.get("description")
    if isinstance(desc, str) and desc.strip():
        return desc.strip()
    deck = issue.get("deck")
    if isinstance(deck, str) and deck.strip():
        return deck.strip()
    return None

def _map_cv_issue_to_comic(issue: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    ext_id = issue.get("id")
    doc: Dict[str, Any] = {
        "title": _best_title(issue),
        "author": None,  # per your demo request
        "onsale_date": _safe_date(issue.get("store_date") or issue.get("cover_date")),
        "format": "Comic",
        "thumbnail_url": _best_thumb(issue),
        "description": _best_description(issue),
        "issue_number": issue.get("issue_number"),
        "marvel_id": ext_id,
    }
    return doc, ext_id

def _sync_one_field(start_iso: str, end_iso: str, *, date_field: str) -> Tuple[int, int]:
    inserted = updated = 0
    offset = 0
    LIMIT = 100
    with Session(engine) as session:
        while True:
            payload = fetch_issues_by_date_range(
                start_iso, end_iso, date_field=date_field, limit=LIMIT, offset=offset
            )
            results: List[Dict[str, Any]] = payload.get("results", [])
            total = payload.get("number_of_total_results", 0)

            vol_ids = [
                (it.get("volume") or {}).get("id")
                for it in results
                if (it.get("volume") or {}).get("id")
            ]
            vol_ids = list(dict.fromkeys(vol_ids))
            vol_map = fetch_volumes_by_ids(vol_ids) if vol_ids else {}

            for issue in results:
                vol_id = (issue.get("volume") or {}).get("id")
                pub_name = ""
                if vol_id is not None:
                    vinfo = vol_map.get(vol_id) or {}
                    publisher = vinfo.get("publisher") or {}
                    pub_name = (publisher.get("name") or "").strip()

                # Only keep Marvel
                if "marvel" not in pub_name.lower():
                    continue

                doc, ext_id = _map_cv_issue_to_comic(issue)
                if not ext_id:
                    continue

                existing = session.exec(
                    select(Comic).where(Comic.marvel_id == ext_id)
                ).first()
                if existing:
                    for k, v in doc.items():
                        setattr(existing, k, v)
                    updated += 1
                else:
                    session.add(Comic(**doc))
                    inserted += 1

            session.commit()
            offset += LIMIT
            if offset >= total:
                break
    return inserted, updated

def cv_sync_range_to_db(
    start_iso: str,
    end_iso: str,
    include_collections: bool = False,  # not used in CV flow
) -> Tuple[int, int]:
    """
    Two passes:
        1) store_date   (real on-sale)
        2) cover_date   (fallback)
    """
    ins1, upd1 = _sync_one_field(start_iso, end_iso, date_field="store_date")
    ins2, upd2 = _sync_one_field(start_iso, end_iso, date_field="cover_date")
    return ins1 + ins2, upd1 + upd2

# Back-compat adapter (old "marvel" name)
def sync_range_to_db(
    start_iso: str, end_iso: str, include_collections: bool = False
) -> Tuple[int, int]:
    return cv_sync_range_to_db(start_iso, end_iso, include_collections=include_collections)
