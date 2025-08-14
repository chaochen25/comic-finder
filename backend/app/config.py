# backend/app/config.py
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

def _load_envs() -> None:
    """
    Load .env from:
      - app/.env  (preferred)
      - backend/.env (fallback)
    """
    here = Path(__file__).resolve().parent
    tried = []
    for candidate in [here / ".env", here.parent / ".env"]:
        tried.append(str(candidate))
        if candidate.exists():
            load_dotenv(candidate)
            return
    # final fallback: allow python-dotenv to scan upwards if nothing found
    load_dotenv()

_load_envs()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./comics.db")

# ComicVine
CV_API_KEY  = os.getenv("CV_API_KEY") or os.getenv("COMICVINE_API_KEY")
CV_BASE_URL = os.getenv("CV_BASE_URL", "https://comicvine.gamespot.com/api")

# CORS for the Vite dev server
CORS_ORIGINS = [
    o.strip() for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if o.strip()
]
