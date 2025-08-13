# backend/app/marvel_client.py
import hashlib, time, os
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from .config import MARVEL_PUBLIC_KEY as PUB, MARVEL_PRIVATE_KEY as PRI, MARVEL_BASE_URL as BASE_URL

load_dotenv()

BASE_URL = os.getenv("MARVEL_BASE_URL", "https://gateway.marvel.com/v1/public")
PUB = os.getenv("MARVEL_PUBLIC_KEY")
PRI = os.getenv("MARVEL_PRIVATE_KEY")

def _auth_params() -> Dict[str, str]:
    ts = str(int(time.time()))
    import hashlib
    m = hashlib.md5()
    m.update((ts + (PRI or "") + (PUB or "")).encode("utf-8"))
    return {"apikey": PUB, "ts": ts, "hash": m.hexdigest()}

def _to_https(url: str) -> str:
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http://"):
        return "https://" + url[len("http://"):]
    return url

def build_thumbnail_url(item: Dict[str, Any], variant: str = "portrait_uncanny") -> Optional[str]:
    """
    Marvel returns: "thumbnail": { "path": "...", "extension": "jpg" }.
    Valid variants include: portrait_uncanny, portrait_incredible, standard_xlarge, detail, etc.
    """
    t = (item or {}).get("thumbnail") or {}
    path = t.get("path")
    ext = t.get("extension") or "jpg"
    if not path:
        return None
    # Skip Marvel's 'image_not_available' placeholder
    if "image_not_available" in path:
        return None
    path = _to_https(path)
    return f"{path}/{variant}.{ext}"

def pick_description(item: Dict[str, Any]) -> Optional[str]:
    """
    Prefer the 'description' field; if absent, try textObjects[0].text (Marvel sometimes stores blurbs there).
    """
    desc = item.get("description")
    if isinstance(desc, str) and desc.strip():
        return desc.strip()
    texts = item.get("textObjects") or []
    if texts:
        t0 = texts[0] or {}
        txt = t0.get("text")
        if isinstance(txt, str) and txt.strip():
            return txt.strip()
    return None

def fetch_comics_by_date_range(start_iso: str, end_iso: str, limit: int = 100, offset: int = 0, include_collections: bool = False) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "dateRange": f"{start_iso},{end_iso}",
        "orderBy": "onsaleDate",
        "limit": limit,
        "offset": offset,
        "noVariants": True,
        # If include_collections is False, prefer single issues
        "formatType": None if include_collections else "comic",
    }
    params = {k: v for k, v in params.items() if v is not None}
    params.update(_auth_params())

    url = f"{BASE_URL}/comics"
    try:
        resp = requests.get(url, params=params, timeout=30)
        # If Marvel returns 4xx/5xx, bubble a clear error instead of crashing
        if not resp.ok:
            detail = {
                "status_code": resp.status_code,
                "url": url,
                "params": {k: v for k, v in params.items() if k not in {"apikey", "hash"}},  # hide secrets
                "body": resp.text[:5000],
            }
            raise HTTPException(status_code=resp.status_code, detail=detail)
        return resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Marvel API request failed: {e}")
