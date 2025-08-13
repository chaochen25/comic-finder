# backend/app/comicvine_client.py
from typing import Dict, Any, List, Set
import math
import requests
from fastapi import HTTPException
from .config import COMICVINE_API_KEY as KEY, COMICVINE_BASE_URL as BASE

UA = {"User-Agent": "ComicFinder/1.0 (+localdev)"}

def _require_key():
    if not KEY:
        raise HTTPException(status_code=500, detail="COMICVINE_API_KEY missing in backend/.env")

def fetch_issues_by_date_range(start_iso: str, end_iso: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """
    Issues filtered by cover_date in [start_iso, end_iso].
    ComicVine returns:
      - status_code == 1 on success
      - number_of_total_results, number_of_page_results, offset, limit
      - results: list of issues
    """
    _require_key()
    params = {
        "api_key": KEY,
        "format": "json",
        "filter": f"cover_date:{start_iso}|{end_iso}",
        "sort": "cover_date:asc",
        "field_list": "id,name,issue_number,cover_date,store_date,image,volume,description,deck,site_detail_url",
        "limit": limit,
        "offset": offset,
    }
    r = requests.get(f"{BASE}/issues/", params=params, headers=UA, timeout=30)
    if not r.ok:
        raise HTTPException(status_code=r.status_code, detail=f"ComicVine issues request failed: {r.text[:500]}")
    data = r.json()
    if data.get("status_code") != 1:
        raise HTTPException(status_code=502, detail=f"ComicVine error: {data.get('error')}")
    return data

def fetch_volumes_by_ids(ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """
    Bulk-lookup volumes so we can check their publishers.
    Returns: { volume_id: {"id":..., "name":..., "publisher": {"id":..., "name":...}} }
    """
    _require_key()
    out: Dict[int, Dict[str, Any]] = {}
    if not ids:
        return out
    # Chunk because ComicVine filter lists shouldn’t be gigantic
    CHUNK = 100
    for i in range(0, len(ids), CHUNK):
        chunk = ids[i:i+CHUNK]
        params = {
            "api_key": KEY,
            "format": "json",
            "filter": "id:" + "|".join(str(x) for x in chunk),
            "field_list": "id,name,publisher",
            "limit": CHUNK,
        }
        r = requests.get(f"{BASE}/volumes/", params=params, headers=UA, timeout=30)
        if not r.ok:
            raise HTTPException(status_code=r.status_code, detail=f"ComicVine volumes request failed: {r.text[:500]}")
        data = r.json()
        if data.get("status_code") != 1:
            raise HTTPException(status_code=502, detail=f"ComicVine volumes error: {data.get('error')}")
        for v in data.get("results", []):
            out[v["id"]] = v
    return out
