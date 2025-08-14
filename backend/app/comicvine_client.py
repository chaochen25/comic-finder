# backend/app/comicvine_client.py
from __future__ import annotations
import os
import time
import math
from typing import Dict, Any, List
import requests

from .config import CV_API_KEY, CV_BASE_URL

UA = "comic-finder/1.0 (+student project)"

class CVError(RuntimeError):
    pass

def _assert_key() -> None:
    if not CV_API_KEY:
        raise CVError("CV_API_KEY missing")

def _get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    _assert_key()
    url = f"{CV_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    base = {
        "api_key": CV_API_KEY,
        "format": "json",
    }
    base.update(params or {})
    r = requests.get(url, params=base, headers={"User-Agent": UA}, timeout=30)
    if r.status_code != 200:
        raise CVError(f"HTTP {r.status_code} for {url}: {r.text[:200]}")
    data = r.json()
    if data.get("status_code") != 1:  # success per ComicVine
        raise CVError(f"ComicVine error: {data.get('error') or data}")
    return data

def fetch_issues_by_date_range(
    start_iso: str,
    end_iso: str,
    *,
    date_field: str,   # "store_date" or "cover_date"
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    GET /issues/ with a date range filter; sorted by the same date field.
    """
    if date_field not in ("store_date", "cover_date"):
        raise CVError("date_field must be store_date or cover_date")

    filters = f"{date_field}:{start_iso}|{end_iso}"

    params = {
        "filter": filters,
        "sort": f"{date_field}:asc",
        "field_list": ",".join([
            "id","issue_number","name","volume",
            "store_date","cover_date",
            "image","description","deck"
        ]),
        "limit": limit,
        "offset": offset,
    }
    return _get("/issues/", params)

def fetch_volumes_by_ids(ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """
    Return {volume_id: {'publisher': {'name': 'Marvel'}}}
    We batch to <= 50 ids per call using /volumes/ with filter=id:id1,id2,...
    """
    out: Dict[int, Dict[str, Any]] = {}
    if not ids:
        return out
    # unique and keep order
    seen = set()
    uniq: List[int] = []
    for i in ids:
        if i not in seen:
            uniq.append(i)
            seen.add(i)

    BATCH = 50
    for i in range(0, len(uniq), BATCH):
        chunk = uniq[i:i+BATCH]
        params = {
            "filter": "id:" + ",".join(str(x) for x in chunk),
            "field_list": "id,publisher",
            "limit": BATCH,
        }
        data = _get("/volumes/", params)
        for v in data.get("results", []):
            vid = v.get("id")
            if isinstance(vid, int):
                out[vid] = v
        # brief politeness delay
        time.sleep(0.15)
    return out
