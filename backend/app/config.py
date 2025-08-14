#config.py
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

#get directory of where files are located
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
    load_dotenv()
#this loads variables for imports
_load_envs()

#database connection for SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./comics.db")

# ComicVine API configs. 
CV_API_KEY  = os.getenv("CV_API_KEY") or os.getenv("COMICVINE_API_KEY")
CV_BASE_URL = os.getenv("CV_BASE_URL", "https://comicvine.gamespot.com/api")

#cross origin function was created with the help of AI
#this function helps tell the backend which frontend URL to call 
CORS_ORIGINS = [
    o.strip() for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if o.strip()
]
