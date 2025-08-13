"""
marvel_client.py
A minimal client for the Marvel API:
- Builds the MD5 hash from ts + private + public (per docs).
- Exposes a function to fetch comics by date range, filtering to single issues.
"""
import hashlib, time, os
from typing import Dict, Any, List, Tuple, Optional
import requests
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

BASE_URL = os.getenv("MARVEL_BASE_URL", "https://gateway.marvel.com/v1/public")
PUB = os.getenv("MARVEL_PUBLIC_KEY")
PRI = os.getenv("MARVEL_PRIVATE_KEY")

def _auth_params() -> Dict[str, str]:
    ts = str(int(time.time()))
    m = hashlib.md5()
    m.update((ts + (PRI or "") + (PUB or "")).encode("utf-8"))
    return {"apikey": PUB, "ts": ts, "hash": m.hexdigest()}

def fetch_comics_by_date_range(start_iso: str, end_iso: str, limit: int = 100, offset: int = 0, include_collections: bool = False) -> Dict[str, Any]:
    params = {
        "dateRange": f"{start_iso},{end_iso}",
        "orderBy": "onsaleDate",
        "limit": limit,
        "offset": offset,
        "noVariants": True,
        "formatType": None if include_collections else "comic",
    }
    params = {k: v for k, v in params.items() if v is not None}
    params.update(_auth_params())

    url = f"{BASE_URL}/comics"
    try:
        resp = requests.get(url, params=params, timeout=20)
        # If Marvel returns 4xx/5xx, bubble it as a FastAPI error (not a crash)
        if not resp.ok:
            detail = {"status_code": resp.status_code, "url": url, "params": params, "body": resp.text}
            raise HTTPException(status_code=resp.status_code, detail=detail)
        return resp.json()
    except requests.RequestException as e:
        # Network/timeout/etc.
        raise HTTPException(status_code=502, detail=f"Marvel API request failed: {e}")